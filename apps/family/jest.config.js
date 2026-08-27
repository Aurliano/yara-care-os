/** @type {import("jest").Config} */
module.exports = {
  testEnvironment: "node",
  testMatch: ["**/__tests__/**/*.test.ts", "**/__tests__/**/*.test.tsx"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^react-native$": "<rootDir>/src/__mocks__/react-native.ts",
    "\\.(png|jpg|jpeg|gif|webp)$": "<rootDir>/src/__mocks__/assetMock.js",
  },
  setupFiles: ["<rootDir>/jest.setup.ts"],
  transform: {
    "^.+\\.(ts|tsx)$": ["babel-jest", { caller: { name: "metro", bundler: "metro", platform: "ios" } }],
  },
};
