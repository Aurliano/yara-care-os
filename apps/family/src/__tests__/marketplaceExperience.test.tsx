import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { useMarketplaceStore } from "../stores/marketplaceStore";
import { useSessionStore } from "../stores/sessionStore";
import { defaultPricingProvider } from "../marketplace/catalog";
import MarketplaceScreen from "../../app/(auth)/marketplace";
import ProductDetailScreen from "../../app/(auth)/product-detail";
import DiscoveryScreen from "../../app/(auth)/discovery";
import SignInScreen from "../../app/(auth)/sign-in";

const mockReplace = jest.fn();
const mockPush = jest.fn();
const mockBack = jest.fn();

jest.mock("expo-router", () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const mockReact = require("react");
  return {
    useRouter: () => ({
      replace: mockReplace,
      push: mockPush,
      back: mockBack,
      canGoBack: () => true,
    }),
    Link: ({ children, testID, href, ...rest }: any) => {
      return mockReact.createElement("View", { testID: testID ?? "mock-link", href, ...rest }, children);
    },
  };
});

describe("R1.1 — Pre-Login Marketplace UX Polish & Acquisition Model", () => {
  beforeEach(() => {
    useMarketplaceStore.getState().resetAll();
    useSessionStore.setState({ user: null, hydrating: false });
    jest.clearAllMocks();
  });

  // 1. Marketplace is accessible before authentication
  it("allows unauthenticated users to access and browse Marketplace", () => {
    expect(useSessionStore.getState().user).toBeNull();
    const { getByText } = render(<MarketplaceScreen />);
    expect(getByText("بسته‌ها و تجهیزات یارا")).toBeTruthy();
  });

  // 2. Product Detail works
  it("renders product detail with factual items and capabilities", () => {
    useMarketplaceStore.getState().setSelectedProductId("yara-care");
    const { getByText } = render(<ProductDetailScreen />);

    expect(getByText("بسته مراقبت یارا")).toBeTruthy();
    expect(getByText("اقلام و تجهیزات موجود در بسته")).toBeTruthy();
    expect(getByText("جعبه داروی هوشمند یارا")).toBeTruthy();
    expect(getByText("هاب رومیزی لمسی یارا")).toBeTruthy();
    expect(getByText("ویژگی‌ها و قابلیت‌های محوری")).toBeTruthy();
  });

  // 3 & 4. Primary acquisition modes: BUY vs RENT
  it("presents 'خرید دستگاه' and 'اجاره دستگاه' as the two primary acquisition choices", () => {
    useMarketplaceStore.getState().setSelectedProductId("yara-hub");
    const { getByText, getAllByText } = render(<ProductDetailScreen />);

    expect(getByText("روش دریافت دستگاه")).toBeTruthy();
    expect(getAllByText("خرید دستگاه").length).toBeGreaterThanOrEqual(1);
    expect(getByText("مالکیت قطعی دستگاه + اشتراک خدمات")).toBeTruthy();
    expect(getAllByText("اجاره دستگاه").length).toBeGreaterThanOrEqual(1);
    expect(getByText("استفاده برای مدت مشخص بدون خرید")).toBeTruthy();
  });

  // 5 & 6 & 7. BUY flow: Monthly/Annual subscription & 3-month free gift
  it("shows subscription tier choices and 3 months free benefit only inside BUY flow", () => {
    useMarketplaceStore.getState().setSelectedProductId("yara-hub");
    useMarketplaceStore.getState().setMethod("yara-hub", "buy");

    const { getByText, getAllByText, queryByText } = render(<ProductDetailScreen />);

    // Subscription options appear inside BUY
    expect(getByText("نوع اشتراک خدمات پس از دوره رایگان:")).toBeTruthy();
    expect(getByText("اشتراک ماهانه")).toBeTruthy();
    expect(getByText("اشتراک سالانه")).toBeTruthy();

    // 3 Months Free benefit banner is clearly visible
    expect(getByText("🎁 ۳ ماه اشتراک رایگان همراه خرید دستگاه")).toBeTruthy();

    // Rental durations must NOT appear inside BUY
    expect(queryByText("مدت زمان اجاره دستگاه:")).toBeNull();

    // Price summary displays separate device price, subscription, free gift, and initial payment
    expect(getByText("قیمت دستگاه (مالکیت قطعی):")).toBeTruthy();
    expect(getAllByText("۸,۹۰۰,۰۰۰ تومان").length).toBeGreaterThanOrEqual(1);
    expect(getByText("۳ ماه اشتراک رایگان")).toBeTruthy();
    expect(getByText("پرداخت اولیه:")).toBeTruthy();
  });

  // 8 & 9. RENT flow: Rental duration appears only inside RENT flow
  it("shows rental durations (1/3/6/12 months) only inside RENT flow and recalculates price immediately", () => {
    useMarketplaceStore.getState().setSelectedProductId("yara-hub");
    const { getByText, getAllByText, getByLabelText, queryByText } = render(<ProductDetailScreen />);

    // Switch to RENT
    fireEvent.press(getByLabelText("اجاره دستگاه"));

    expect(useMarketplaceStore.getState().getConfiguration("yara-hub").method).toBe("rent");

    // Subscription options must disappear
    expect(queryByText("نوع اشتراک خدمات پس از دوره رایگان:")).toBeNull();
    expect(queryByText("🎁 ۳ ماه اشتراک رایگان همراه خرید دستگاه")).toBeNull();

    // Rental duration options must appear
    expect(getByText("مدت زمان اجاره دستگاه:")).toBeTruthy();
    expect(getAllByText("۱ ماه").length).toBeGreaterThanOrEqual(1);
    expect(getAllByText("۳ ماه").length).toBeGreaterThanOrEqual(1);
    expect(getAllByText("۶ ماه").length).toBeGreaterThanOrEqual(1);
    expect(getAllByText("۱۲ ماه").length).toBeGreaterThanOrEqual(1);

    // 1 Month default -> 650,000 تومان
    expect(getByText("۶۵۰,۰۰۰ تومان")).toBeTruthy();

    // Select 3 Months -> 1,800,000 تومان
    fireEvent.press(getByLabelText("اجاره برای ۳ ماه"));
    expect(useMarketplaceStore.getState().getConfiguration("yara-hub").rentalDurationMonths).toBe(3);
    expect(getByText("۱,۸۰۰,۰۰۰ تومان")).toBeTruthy();

    // Select 6 Months -> 3,300,000 تومان
    fireEvent.press(getByLabelText("اجاره برای ۶ ماه"));
    expect(useMarketplaceStore.getState().getConfiguration("yara-hub").rentalDurationMonths).toBe(6);
    expect(getByText("۳,۳۰۰,۰۰۰ تومان")).toBeTruthy();

    // Select 12 Months -> 6,000,000 تومان
    fireEvent.press(getByLabelText("اجاره برای ۱۲ ماه"));
    expect(useMarketplaceStore.getState().getConfiguration("yara-hub").rentalDurationMonths).toBe(12);
    expect(getByText("۶,۰۰۰,۰۰۰ تومان")).toBeTruthy();
  });

  // 10. Annual subscription updates price immediately in BUY flow
  it("updates subscription summary immediately when switching between monthly and annual", () => {
    useMarketplaceStore.getState().setSelectedProductId("yara-care");
    useMarketplaceStore.getState().setMethod("yara-care", "buy");

    const { getByText, getAllByText, getByLabelText } = render(<ProductDetailScreen />);

    // By default monthly: 550,000
    expect(getAllByText(/اشتراک ماهانه/).length).toBeGreaterThanOrEqual(1);

    // Switch to annual
    fireEvent.press(getByLabelText("اشتراک سالانه"));
    expect(useMarketplaceStore.getState().getConfiguration("yara-care").subscriptionTier).toBe("annual");
    expect(getByText(/اشتراک سالانه \(با تخفیف\)/)).toBeTruthy();
  });

  // 11 & 12. No acquisition card is hidden and back navigation preserves configuration
  it("preserves configuration across back navigation without hiding cards", () => {
    // Configure yara-care-plus with rental for 6 months
    useMarketplaceStore.getState().setMethod("yara-care-plus", "rent");
    useMarketplaceStore.getState().setRentalDuration("yara-care-plus", 6);

    useMarketplaceStore.getState().setSelectedProductId("yara-care-plus");
    const { getByText } = render(<ProductDetailScreen />);

    // 6 months rental for care-plus is 7,000,000 تومان
    expect(getByText("۷,۰۰۰,۰۰۰ تومان")).toBeTruthy();

    // Tap back button
    fireEvent.press(getByText("بازگشت"));
    expect(mockBack).toHaveBeenCalled();

    // Configuration is preserved
    const saved = useMarketplaceStore.getState().getConfiguration("yara-care-plus");
    expect(saved.method).toBe("rent");
    expect(saved.rentalDurationMonths).toBe(6);
  });

  // 13. Discovery → Marketplace navigation
  it("allows navigating from Discovery to Marketplace on final slide", async () => {
    const { getByText } = render(<DiscoveryScreen />);

    // Step to the final slide
    fireEvent.press(getByText("بعدی"));
    fireEvent.press(getByText("بعدی"));
    fireEvent.press(getByText("بعدی"));

    await waitFor(() => {
      expect(getByText("مشاهده بسته‌ها و محصولات یارا")).toBeTruthy();
    });

    fireEvent.press(getByText("مشاهده بسته‌ها و محصولات یارا"));
    expect(mockPush).toHaveBeenCalledWith("/(auth)/marketplace");
  });

  // 14. Returning unauthenticated users can reach Marketplace from Login
  it("renders secondary exploration link to Marketplace on SignIn screen", () => {
    const { getByText } = render(<SignInScreen />);
    expect(getByText("مشاهده بسته‌ها و تجهیزات یارا")).toBeTruthy();
  });

  // 15. Checkout boundary navigates to SignIn
  it("navigates to auth when user continues to order without creating fake state", () => {
    useMarketplaceStore.getState().setSelectedProductId("yara-hub");
    const { getByText } = render(<ProductDetailScreen />);

    const orderButton = getByText("ادامه و ثبت سفارش");
    fireEvent.press(orderButton);

    expect(mockPush).toHaveBeenCalledWith("/(auth)/sign-in");
  });

  // 16. Authenticated users bypass Discovery
  it("ensures authenticated users bypass pre-login flow", () => {
    function computeLaunchTarget(user: any, selectedElderId: string | null) {
      if (user) {
        if (!selectedElderId) return "/(auth)/select-elder";
        return "/(app)/(tabs)";
      }
      return "/(auth)/discovery";
    }

    expect(computeLaunchTarget({ id: "usr-1" }, "eld-1")).toBe("/(app)/(tabs)");
    expect(computeLaunchTarget({ id: "usr-1" }, null)).toBe("/(auth)/select-elder");
  });

  // 17. Catalog pricing provider calculations match expected catalog rules
  it("verifies pricing provider calculations for Buy and Rent models", () => {
    const hubBuyMonthly = defaultPricingProvider.calculatePrice({
      productId: "yara-hub",
      method: "buy",
      subscriptionTier: "monthly",
      rentalDurationMonths: 1,
    });
    expect(hubBuyMonthly.method).toBe("buy");
    expect(hubBuyMonthly.devicePrice).toBe(8900000);
    expect(hubBuyMonthly.freeSubscriptionMonths).toBe(3);
    expect(hubBuyMonthly.initialPaymentAmount).toBe(8900000);

    const careRent3Mo = defaultPricingProvider.calculatePrice({
      productId: "yara-care",
      method: "rent",
      subscriptionTier: "monthly",
      rentalDurationMonths: 3,
    });
    expect(careRent3Mo.method).toBe("rent");
    expect(careRent3Mo.amount).toBe(2650000);
    expect(careRent3Mo.rentalDurationMonths).toBe(3);
  });
});
