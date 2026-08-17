import fs from "node:fs";
import path from "node:path";

const COMMUNICATION_DIR = path.resolve(__dirname, "../communication");

describe("Family communication architecture", () => {
  it("never calls Skyroom REST or stores a vendor API key", () => {
    const files = fs.readdirSync(COMMUNICATION_DIR);
    expect(files.length).toBeGreaterThan(0);
    for (const file of files) {
      const text = fs.readFileSync(path.join(COMMUNICATION_DIR, file), "utf8");
      expect(text).not.toMatch(/skyroom\.online\/skyroom\/api/i);
      expect(text).not.toMatch(/skyroom_api_key/i);
      expect(text).not.toMatch(/apikey-/i);
      expect(text).not.toMatch(/SKYROOM_API_KEY/);
    }
  });
});
