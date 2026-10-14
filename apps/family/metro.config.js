const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

if (config.resolver.emptyModulePath) {
  const drive = __dirname.slice(0, 2);
  config.resolver.emptyModulePath = config.resolver.emptyModulePath.replace(/^[a-zA-Z]:/, drive);
}

const originalResolveRequest = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (typeof moduleName === "string" && /^[a-zA-Z]:\\[a-zA-Z]:\\/.test(moduleName)) {
    moduleName = moduleName.slice(3);
  }
  const result = originalResolveRequest
    ? originalResolveRequest(context, moduleName, platform)
    : context.resolveRequest(context, moduleName, platform);

  if (result && result.type === "sourceFile" && typeof result.filePath === "string") {
    if (/^[a-zA-Z]:\\[a-zA-Z]:\\/.test(result.filePath)) {
      result.filePath = result.filePath.slice(3);
    }
  }
  return result;
};

module.exports = config;
