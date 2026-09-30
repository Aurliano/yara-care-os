import { create } from "zustand";
import {
  type PackageConfiguration,
  type AcquisitionMethod,
  type SubscriptionTier,
  type RentalDurationMonths,
  defaultPricingProvider,
  type CalculatedPrice,
} from "../marketplace/catalog";

interface MarketplaceState {
  selectedProductId: string;
  configurations: Record<string, PackageConfiguration>;
  setSelectedProductId: (id: string) => void;
  getConfiguration: (productId: string) => PackageConfiguration;
  setMethod: (productId: string, method: AcquisitionMethod) => void;
  setSubscriptionTier: (productId: string, tier: SubscriptionTier) => void;
  setRentalDuration: (productId: string, duration: RentalDurationMonths) => void;
  setMode: (productId: string, mode: "purchase" | "subscription_monthly" | "subscription_annual" | "rental") => void;
  getCalculatedPrice: (productId: string) => CalculatedPrice;
  resetAll: () => void;
}

const DEFAULT_CONFIGS: Record<string, PackageConfiguration> = {
  "yara-hub": {
    productId: "yara-hub",
    method: "buy",
    subscriptionTier: "monthly",
    rentalDurationMonths: 1,
  },
  "yara-care": {
    productId: "yara-care",
    method: "buy",
    subscriptionTier: "monthly",
    rentalDurationMonths: 1,
  },
  "yara-care-plus": {
    productId: "yara-care-plus",
    method: "buy",
    subscriptionTier: "monthly",
    rentalDurationMonths: 1,
  },
};

export const useMarketplaceStore = create<MarketplaceState>((set, get) => ({
  selectedProductId: "yara-hub",
  configurations: { ...DEFAULT_CONFIGS },

  setSelectedProductId(id: string) {
    set({ selectedProductId: id });
  },

  getConfiguration(productId: string): PackageConfiguration {
    const existing = get().configurations[productId];
    if (existing) return existing;

    const fallback: PackageConfiguration = {
      productId,
      method: "buy",
      subscriptionTier: "monthly",
      rentalDurationMonths: 1,
    };
    return fallback;
  },

  setMethod(productId: string, method: AcquisitionMethod) {
    set((state) => {
      const current = state.configurations[productId] ?? {
        productId,
        method: "buy",
        subscriptionTier: "monthly",
        rentalDurationMonths: 1,
      };
      return {
        configurations: {
          ...state.configurations,
          [productId]: {
            ...current,
            method,
          },
        },
      };
    });
  },

  setSubscriptionTier(productId: string, tier: SubscriptionTier) {
    set((state) => {
      const current = state.configurations[productId] ?? {
        productId,
        method: "buy",
        subscriptionTier: "monthly",
        rentalDurationMonths: 1,
      };
      return {
        configurations: {
          ...state.configurations,
          [productId]: {
            ...current,
            subscriptionTier: tier,
          },
        },
      };
    });
  },

  setRentalDuration(productId: string, duration: RentalDurationMonths) {
    set((state) => {
      const current = state.configurations[productId] ?? {
        productId,
        method: "rent",
        subscriptionTier: "monthly",
        rentalDurationMonths: 1,
      };
      return {
        configurations: {
          ...state.configurations,
          [productId]: {
            ...current,
            rentalDurationMonths: duration,
          },
        },
      };
    });
  },

  setMode(productId: string, mode: "purchase" | "subscription_monthly" | "subscription_annual" | "rental") {
    if (mode === "rental") {
      get().setMethod(productId, "rent");
    } else if (mode === "purchase") {
      get().setMethod(productId, "buy");
    } else if (mode === "subscription_monthly") {
      get().setMethod(productId, "buy");
      get().setSubscriptionTier(productId, "monthly");
    } else if (mode === "subscription_annual") {
      get().setMethod(productId, "buy");
      get().setSubscriptionTier(productId, "annual");
    }
  },

  getCalculatedPrice(productId: string): CalculatedPrice {
    const config = get().getConfiguration(productId);
    return defaultPricingProvider.calculatePrice(config);
  },

  resetAll() {
    set({
      selectedProductId: "yara-hub",
      configurations: { ...DEFAULT_CONFIGS },
    });
  },
}));
