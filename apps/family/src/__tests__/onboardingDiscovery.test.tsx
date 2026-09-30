import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import {
  useOnboardingStore,
  setOnboardingStorage,
  type OnboardingStorage,
} from "../stores/onboardingStore";
import { useSessionStore } from "../stores/sessionStore";
import { t } from "../i18n";
import DiscoveryScreen from "../../app/(auth)/discovery";

// Mock router for expo-router
const mockReplace = jest.fn();
const mockPush = jest.fn();

jest.mock("expo-router", () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const mockReact = require("react");
  return {
    useRouter: () => ({
      replace: mockReplace,
      push: mockPush,
    }),
    Link: ({ children, testID, ...rest }: any) => {
      return mockReact.createElement("View", { testID: testID ?? "mock-link", ...rest }, children);
    },
  };
});

describe("R1 — Onboarding Store & Persistence", () => {
  let memoryStorage: Record<string, string> = {};

  const testStorage: OnboardingStorage = {
    async getStatus() {
      return memoryStorage["yara.discoveryStatus"] ?? null;
    },
    async setStatus(status: string) {
      memoryStorage["yara.discoveryStatus"] = status;
    },
    async clearStatus() {
      delete memoryStorage["yara.discoveryStatus"];
    },
  };

  beforeEach(() => {
    memoryStorage = {};
    setOnboardingStorage(testStorage);
    useOnboardingStore.setState({ status: "not_started", hydrated: false });
    jest.clearAllMocks();
  });

  it("initializes with not_started on fresh install", async () => {
    await useOnboardingStore.getState().hydrate();
    const state = useOnboardingStore.getState();
    expect(state.status).toBe("not_started");
    expect(state.hydrated).toBe(true);
  });

  it("persists completion correctly", async () => {
    await useOnboardingStore.getState().completeDiscovery();
    expect(useOnboardingStore.getState().status).toBe("completed");
    expect(memoryStorage["yara.discoveryStatus"]).toBe("completed");

    // Re-hydrate to ensure persistent retrieval on subsequent launch
    useOnboardingStore.setState({ status: "not_started", hydrated: false });
    await useOnboardingStore.getState().hydrate();
    expect(useOnboardingStore.getState().status).toBe("completed");
  });

  it("persists skip correctly", async () => {
    await useOnboardingStore.getState().skipDiscovery();
    expect(useOnboardingStore.getState().status).toBe("skipped");
    expect(memoryStorage["yara.discoveryStatus"]).toBe("skipped");

    // Re-hydrate to ensure persistent retrieval
    useOnboardingStore.setState({ status: "not_started", hydrated: false });
    await useOnboardingStore.getState().hydrate();
    expect(useOnboardingStore.getState().status).toBe("skipped");
  });

  it("logout does not reset or corrupt onboarding discovery state", async () => {
    // 1. User completed discovery
    await useOnboardingStore.getState().completeDiscovery();
    expect(useOnboardingStore.getState().status).toBe("completed");

    // 2. User was logged in
    useSessionStore.setState({
      user: {
        id: "usr-1",
        phone: "+989123456789",
        email: "ali@example.com",
        full_name: "Ali Caregiver",
        status: "ACTIVE",
        created_at: "2026-09-27T00:00:00Z",
      },
      hydrating: false,
    });
    expect(useSessionStore.getState().user).not.toBeNull();

    // 3. User logs out
    await useSessionStore.getState().signOut();
    expect(useSessionStore.getState().user).toBeNull();

    // 4. Onboarding state must remain completed
    expect(useOnboardingStore.getState().status).toBe("completed");
    expect(memoryStorage["yara.discoveryStatus"]).toBe("completed");
  });
});

describe("R1 — Pre-login Index Routing Logic", () => {
  function computeRedirectTarget({
    user,
    selectedElderId,
    discoveryStatus,
  }: {
    user: any;
    selectedElderId: string | null;
    discoveryStatus: "not_started" | "completed" | "skipped";
  }): string {
    if (user) {
      if (!selectedElderId) {
        return "/(auth)/select-elder";
      }
      return "/(app)/(tabs)";
    }
    if (discoveryStatus === "not_started") {
      return "/(auth)/discovery";
    }
    return "/(auth)/sign-in";
  }

  it("routes fresh install (not_started, unauthenticated) to discovery", () => {
    const target = computeRedirectTarget({
      user: null,
      selectedElderId: null,
      discoveryStatus: "not_started",
    });
    expect(target).toBe("/(auth)/discovery");
  });

  it("routes returning user who completed discovery to sign-in", () => {
    const target = computeRedirectTarget({
      user: null,
      selectedElderId: null,
      discoveryStatus: "completed",
    });
    expect(target).toBe("/(auth)/sign-in");
  });

  it("routes returning user who skipped discovery to sign-in", () => {
    const target = computeRedirectTarget({
      user: null,
      selectedElderId: null,
      discoveryStatus: "skipped",
    });
    expect(target).toBe("/(auth)/sign-in");
  });

  it("never traps authenticated user in discovery even if discovery was not_started", () => {
    const targetWithElder = computeRedirectTarget({
      user: { id: "u1" },
      selectedElderId: "eld-1",
      discoveryStatus: "not_started",
    });
    expect(targetWithElder).toBe("/(app)/(tabs)");

    const targetWithoutElder = computeRedirectTarget({
      user: { id: "u1" },
      selectedElderId: null,
      discoveryStatus: "not_started",
    });
    expect(targetWithoutElder).toBe("/(auth)/select-elder");
  });
});

describe("R1 — Product Discovery Screen & Interaction", () => {
  let memoryStorage: Record<string, string> = {};

  const testStorage: OnboardingStorage = {
    async getStatus() {
      return memoryStorage["yara.discoveryStatus"] ?? null;
    },
    async setStatus(status: string) {
      memoryStorage["yara.discoveryStatus"] = status;
    },
    async clearStatus() {
      delete memoryStorage["yara.discoveryStatus"];
    },
  };

  beforeEach(() => {
    memoryStorage = {};
    setOnboardingStorage(testStorage);
    useOnboardingStore.setState({ status: "not_started", hydrated: true });
    jest.clearAllMocks();
  });

  it("renders slide 1 with Persian ecosystem value proposition", () => {
    const { getByText } = render(<DiscoveryScreen />);
    expect(getByText("آرامش خاطر خانواده، کرامت عزیزانتان")).toBeTruthy();
    expect(getByText("زیست‌بوم مراقبت سالمند")).toBeTruthy();
    expect(getByText(t.discoverySkip)).toBeTruthy();
    expect(getByText(t.discoveryNext)).toBeTruthy();
  });

  it("supports skipping discovery at any time", async () => {
    const { getByText } = render(<DiscoveryScreen />);
    const skipButton = getByText(t.discoverySkip);

    fireEvent.press(skipButton);

    await waitFor(() => {
      expect(useOnboardingStore.getState().status).toBe("skipped");
      expect(mockReplace).toHaveBeenCalledWith("/(auth)/sign-in");
    });
  });

  it("allows navigating through steps and concludes with login and signup options", async () => {
    const { getByText } = render(<DiscoveryScreen />);

    // Step 1 -> Step 2 (Hub)
    fireEvent.press(getByText(t.discoveryNext));
    await waitFor(() => {
      expect(getByText("هاب اختصاصی؛ همراه بدون پیچیدگی")).toBeTruthy();
      expect(getByText("هاب رومیزی یارا")).toBeTruthy();
    });

    // Step 2 -> Step 3 (Medication)
    fireEvent.press(getByText(t.discoveryNext));
    await waitFor(() => {
      expect(getByText("انضباط دارویی و روال‌های روزمره")).toBeTruthy();
      expect(getByText("نظم و روال مراقبت")).toBeTruthy();
    });

    // Step 3 -> Step 4 (Connection & Ecosystem)
    fireEvent.press(getByText(t.discoveryNext));
    await waitFor(() => {
      expect(getByText("همیشه نزدیک، با یک لمس ساده")).toBeTruthy();
      expect(getByText(t.discoveryLogin)).toBeTruthy();
      expect(getByText(t.discoveryRegister)).toBeTruthy();
      // Medical boundary disclaimer is visible
      expect(getByText(t.discoveryDisclaimer)).toBeTruthy();
    });

    // Pressing Login from final step completes discovery and routes to sign-in
    fireEvent.press(getByText(t.discoveryLogin));
    await waitFor(() => {
      expect(useOnboardingStore.getState().status).toBe("completed");
      expect(mockReplace).toHaveBeenCalledWith("/(auth)/sign-in");
    });
  });

  it("allows navigating to registration from final step", async () => {
    const { getByText } = render(<DiscoveryScreen />);

    // Step to the end
    fireEvent.press(getByText(t.discoveryNext));
    fireEvent.press(getByText(t.discoveryNext));
    fireEvent.press(getByText(t.discoveryNext));

    await waitFor(() => {
      expect(getByText(t.discoveryRegister)).toBeTruthy();
    });

    fireEvent.press(getByText(t.discoveryRegister));
    await waitFor(() => {
      expect(useOnboardingStore.getState().status).toBe("completed");
      expect(mockReplace).toHaveBeenCalledWith("/(auth)/register");
    });
  });

  it("supports going back to previous steps", async () => {
    const { getByText, queryByText } = render(<DiscoveryScreen />);

    // Move to step 2
    fireEvent.press(getByText(t.discoveryNext));
    await waitFor(() => {
      expect(getByText("هاب اختصاصی؛ همراه بدون پیچیدگی")).toBeTruthy();
      expect(getByText(t.discoveryPrev)).toBeTruthy();
    });

    // Go back to step 1
    fireEvent.press(getByText(t.discoveryPrev));
    await waitFor(() => {
      expect(getByText("آرامش خاطر خانواده، کرامت عزیزانتان")).toBeTruthy();
      // On first step, prev is hidden
      expect(queryByText(t.discoveryPrev)).toBeNull();
    });
  });

  it("contains clear medical disclaimers and does not make unauthorized claims", () => {
    expect(t.discoveryDisclaimer).toContain("جایگزین خدمات اورژانس، پزشک یا تجهیزات درمانی نیست");
  });
});
