"use strict";

const { app, BrowserWindow, session } = require("electron");
const path = require("path");

const DEFAULT_RUNTIME_URL = "http://127.0.0.1:8765";
const ALLOW_NON_LOOPBACK = process.env.JARVIS_ELECTRON_ALLOW_NON_LOOPBACK === "1";

function runtimeUrl() {
  const value = process.env.JARVIS_RUNTIME_URL || DEFAULT_RUNTIME_URL;
  const parsed = new URL(value);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("JARVIS_RUNTIME_URL must use http or https");
  }
  if (!ALLOW_NON_LOOPBACK && !isLoopbackHost(parsed.hostname)) {
    throw new Error("Electron HUD loads loopback runtime by default; set JARVIS_ELECTRON_ALLOW_NON_LOOPBACK=1 for approved private-network use");
  }
  return parsed;
}

function isLoopbackHost(hostname) {
  return ["127.0.0.1", "localhost", "::1", "[::1]"].includes(hostname);
}

function sameOrigin(left, right) {
  return left.protocol === right.protocol && left.host === right.host;
}

function createWindow() {
  const target = runtimeUrl();
  const win = new BrowserWindow({
    width: 1440,
    height: 1000,
    minWidth: 1180,
    minHeight: 760,
    backgroundColor: "#020713",
    title: "Jarvis Codex",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });

  win.setMenu(null);
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  win.webContents.on("will-navigate", (event, nextUrl) => {
    if (!sameOrigin(new URL(nextUrl), target)) {
      event.preventDefault();
    }
  });

  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    const requester = new URL(webContents.getURL());
    const allowed = sameOrigin(requester, target) && permission === "media";
    callback(allowed);
  });

  win.loadURL(target.toString());
  return win;
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

module.exports = {
  DEFAULT_RUNTIME_URL,
  isLoopbackHost,
  sameOrigin
};
