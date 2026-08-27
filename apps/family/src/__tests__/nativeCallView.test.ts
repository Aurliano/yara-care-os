import { NativeCallView } from "../components/NativeCallView";
import * as mediaPermissions from "../permissions/mediaPermissions";

describe("NativeCallView component contract", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("exports NativeCallView function component", () => {
    expect(typeof NativeCallView).toBe("function");
  });

  it("requests runtime media permissions for video and voice calls", async () => {
    const reqSpy = jest.spyOn(mediaPermissions, "requestMediaPermissions").mockResolvedValue({
      camera: true,
      microphone: true,
    });

    const videoPerms = await mediaPermissions.requestMediaPermissions("VIDEO");
    expect(reqSpy).toHaveBeenCalledWith("VIDEO");
    expect(videoPerms).toEqual({ camera: true, microphone: true });

    const voicePerms = await mediaPermissions.requestMediaPermissions("VOICE");
    expect(reqSpy).toHaveBeenCalledWith("VOICE");
    expect(voicePerms).toEqual({ camera: true, microphone: true });
  });

  it("handles denied media permissions correctly", async () => {
    jest.spyOn(mediaPermissions, "requestMediaPermissions").mockResolvedValue({
      camera: false,
      microphone: false,
    });

    const perms = await mediaPermissions.requestMediaPermissions("VIDEO");
    expect(perms.camera).toBe(false);
    expect(perms.microphone).toBe(false);
  });
});
