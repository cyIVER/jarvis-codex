using NAudio.CoreAudioApi;
using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace JarvisMicRecorder;

internal static class Program
{
    private const int TargetSampleRate = 16000;
    private const int MinSeconds = 1;
    private const int MaxSeconds = 300;

    private static async Task<int> Main(string[] args)
    {
        try
        {
            var options = RecorderOptions.Parse(args);
            await RecordOnceAsync(options);
            return 0;
        }
        catch (ArgumentException exc)
        {
            Console.Error.WriteLine(exc.Message);
            PrintUsage();
            return 2;
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine(exc.Message);
            return 1;
        }
    }

    private static async Task RecordOnceAsync(RecorderOptions options)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(options.OutputFile) ?? ".");

        var tempFile = Path.Combine(
            Path.GetDirectoryName(options.OutputFile) ?? ".",
            $".jarvis-mic-{Guid.NewGuid():N}.capture.wav"
        );

        try
        {
            using var capture = CreateCapture(options);
            await CaptureToTempWavAsync(capture, tempFile, options.Seconds);
            ConvertToWhisperFriendlyWav(tempFile, options.OutputFile);

            var info = new FileInfo(options.OutputFile);
            if (!info.Exists || info.Length == 0)
            {
                throw new InvalidOperationException("recorder did not write audio output");
            }
        }
        finally
        {
            TryDelete(tempFile);
        }
    }

    private static WasapiCapture CreateCapture(RecorderOptions options)
    {
        if (options.DeviceIndex is null)
        {
            return new WasapiCapture();
        }

        using var enumerator = new MMDeviceEnumerator();
        var devices = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
        var index = options.DeviceIndex.Value;
        if (index < 0 || index >= devices.Count)
        {
            throw new ArgumentException($"capture device index is out of range: {index}");
        }
        return new WasapiCapture(devices[index]);
    }

    private static async Task CaptureToTempWavAsync(WasapiCapture capture, string tempFile, int seconds)
    {
        var stopped = new TaskCompletionSource<object?>(TaskCreationOptions.RunContinuationsAsynchronously);
        using var writer = new WaveFileWriter(tempFile, capture.WaveFormat);

        capture.DataAvailable += (_, eventArgs) =>
        {
            if (eventArgs.BytesRecorded > 0)
            {
                writer.Write(eventArgs.Buffer, 0, eventArgs.BytesRecorded);
            }
        };
        capture.RecordingStopped += (_, eventArgs) =>
        {
            if (eventArgs.Exception is not null)
            {
                stopped.TrySetException(eventArgs.Exception);
            }
            else
            {
                stopped.TrySetResult(null);
            }
        };

        capture.StartRecording();
        await Task.Delay(TimeSpan.FromSeconds(seconds));
        capture.StopRecording();
        await stopped.Task;
    }

    private static void ConvertToWhisperFriendlyWav(string sourceFile, string outputFile)
    {
        using var reader = new AudioFileReader(sourceFile);
        ISampleProvider sampleProvider = reader;

        if (reader.WaveFormat.Channels == 2)
        {
            sampleProvider = new StereoToMonoSampleProvider(sampleProvider)
            {
                LeftVolume = 0.5f,
                RightVolume = 0.5f,
            };
        }
        else if (reader.WaveFormat.Channels != 1)
        {
            sampleProvider = new MonoDownmixSampleProvider(sampleProvider);
        }

        if (sampleProvider.WaveFormat.SampleRate != TargetSampleRate)
        {
            sampleProvider = new WdlResamplingSampleProvider(sampleProvider, TargetSampleRate);
        }

        WaveFileWriter.CreateWaveFile16(outputFile, sampleProvider);
    }

    private static void TryDelete(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch
        {
            // Temp capture cleanup should not hide the recording result.
        }
    }

    private static void PrintUsage()
    {
        Console.Error.WriteLine("Usage: JarvisMicRecorder.exe --output-file <path.wav> --seconds <1-300> [--device-index <n>]");
    }

    private sealed record RecorderOptions(string OutputFile, int Seconds, int? DeviceIndex)
    {
        public static RecorderOptions Parse(string[] args)
        {
            string? outputFile = null;
            int? seconds = null;
            int? deviceIndex = null;

            for (var index = 0; index < args.Length; index++)
            {
                var arg = args[index];
                switch (arg)
                {
                    case "--output-file":
                        outputFile = RequireValue(args, ref index, arg);
                        break;
                    case "--seconds":
                        seconds = ParseInt(RequireValue(args, ref index, arg), arg);
                        break;
                    case "--device-index":
                        deviceIndex = ParseInt(RequireValue(args, ref index, arg), arg);
                        break;
                    case "--help":
                    case "-h":
                        throw new ArgumentException("Jarvis Windows mic recorder");
                    default:
                        throw new ArgumentException($"unknown argument: {arg}");
                }
            }

            if (string.IsNullOrWhiteSpace(outputFile))
            {
                throw new ArgumentException("--output-file is required");
            }
            if (seconds is null)
            {
                throw new ArgumentException("--seconds is required");
            }
            if (seconds < MinSeconds || seconds > MaxSeconds)
            {
                throw new ArgumentException("--seconds must be between 1 and 300");
            }

            return new RecorderOptions(Path.GetFullPath(outputFile), seconds.Value, deviceIndex);
        }

        private static string RequireValue(string[] args, ref int index, string name)
        {
            if (index + 1 >= args.Length || args[index + 1].StartsWith("--", StringComparison.Ordinal))
            {
                throw new ArgumentException($"{name} requires a value");
            }
            index++;
            return args[index];
        }

        private static int ParseInt(string value, string name)
        {
            if (!int.TryParse(value, out var parsed))
            {
                throw new ArgumentException($"{name} must be an integer");
            }
            return parsed;
        }
    }

    private sealed class MonoDownmixSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider source;
        private readonly int sourceChannels;
        private readonly float[] sourceBuffer;

        public MonoDownmixSampleProvider(ISampleProvider source)
        {
            this.source = source;
            sourceChannels = source.WaveFormat.Channels;
            if (sourceChannels < 1)
            {
                throw new InvalidOperationException("source must have at least one channel");
            }
            sourceBuffer = new float[8192 * sourceChannels];
            WaveFormat = WaveFormat.CreateIeeeFloatWaveFormat(source.WaveFormat.SampleRate, 1);
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            var framesRequested = count;
            var samplesRequested = Math.Min(sourceBuffer.Length, framesRequested * sourceChannels);
            var samplesRead = source.Read(sourceBuffer, 0, samplesRequested);
            var framesRead = samplesRead / sourceChannels;

            for (var frame = 0; frame < framesRead; frame++)
            {
                float sum = 0;
                var baseIndex = frame * sourceChannels;
                for (var channel = 0; channel < sourceChannels; channel++)
                {
                    sum += sourceBuffer[baseIndex + channel];
                }
                buffer[offset + frame] = sum / sourceChannels;
            }

            return framesRead;
        }
    }
}
