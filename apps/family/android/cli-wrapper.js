#!/usr/bin/env node
const fs = require("fs");

function fixPath(p) {
  if (typeof p === "string" && /^[a-zA-Z]:\\[a-zA-Z]:\\/.test(p)) {
    return p.slice(3);
  }
  return p;
}

const origReadFileSync = fs.readFileSync;
fs.readFileSync = function (file, ...args) {
  return origReadFileSync.call(fs, fixPath(file), ...args);
};

const origStatSync = fs.statSync;
fs.statSync = function (file, ...args) {
  return origStatSync.call(fs, fixPath(file), ...args);
};

const origLstatSync = fs.lstatSync;
fs.lstatSync = function (file, ...args) {
  return origLstatSync.call(fs, fixPath(file), ...args);
};

const origExistsSync = fs.existsSync;
fs.existsSync = function (file) {
  return origExistsSync.call(fs, fixPath(file));
};

try {
  const ModuleResolution = require("metro/src/node-haste/DependencyGraph/ModuleResolution");
  const origResolve = ModuleResolution.prototype.resolveDependency;
  ModuleResolution.prototype.resolveDependency = function (...args) {
    const res = origResolve.apply(this, args);
    if (res && res.type === "sourceFile" && res.filePath) {
      res.filePath = fixPath(res.filePath);
    }
    return res;
  };
} catch (_) {}

try {
  const DependencyGraph = require("metro/src/node-haste/DependencyGraph");
  const origGetSha1 = DependencyGraph.prototype.getOrComputeSha1;
  DependencyGraph.prototype.getOrComputeSha1 = function (mixedPath) {
    return origGetSha1.call(this, fixPath(mixedPath));
  };
} catch (_) {}

for (let i = 0; i < process.argv.length; i++) {
  if (process.argv[i].includes("expo-router\\entry")) {
    process.argv[i] = process.argv[i].replace(/\\/g, "/");
  }
}

require("@expo/cli/build/bin/cli");
