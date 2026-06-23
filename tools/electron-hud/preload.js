"use strict";

const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("jarvisElectron", {
  shellAuthority: false,
  runtimeUrl: process.env.JARVIS_RUNTIME_URL || "http://127.0.0.1:8765",
  client: "electron-hud"
});
