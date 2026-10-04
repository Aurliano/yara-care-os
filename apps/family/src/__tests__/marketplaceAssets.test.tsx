import React from "react";
import { render } from "@testing-library/react-native";
import {
  ProductAsset,
  PRODUCT_IMAGE_SOURCES,
  resolveSemanticAssetId,
  type SemanticProductAssetId,
  type ProductAssetId,
} from "../marketplace/assets";

describe("Marketplace Photographic Assets & Semantic Resolution", () => {
  const ALL_SEMANTIC_IDS: SemanticProductAssetId[] = [
    "yara-hub-hero",
    "yara-hub-lifestyle",
    "yara-hub-ui",
    "smart-pillbox-hero",
    "smart-pillbox-lifestyle",
    "yara-wearable-hero",
    "yara-wearable-lifestyle",
    "yara-care-bundle",
    "yara-care-plus-bundle",
    "yara-hub-pillbox-ecosystem",
    "yara-full-ecosystem",
    "yara-marketplace-hero",
  ];

  it("has valid required image sources for all 12 semantic assets", () => {
    expect(ALL_SEMANTIC_IDS).toHaveLength(12);
    for (const assetId of ALL_SEMANTIC_IDS) {
      expect(PRODUCT_IMAGE_SOURCES[assetId]).toBeDefined();
    }
  });

  it("correctly maps legacy product asset IDs to modern semantic IDs", () => {
    expect(resolveSemanticAssetId("yara-hub")).toBe("yara-hub-hero");
    expect(resolveSemanticAssetId("yara-care")).toBe("yara-care-bundle");
    expect(resolveSemanticAssetId("yara-care-plus")).toBe("yara-care-plus-bundle");
    expect(resolveSemanticAssetId("smart-pillbox")).toBe("smart-pillbox-hero");
    expect(resolveSemanticAssetId("wearable")).toBe("yara-wearable-hero");
  });

  it("renders a semantic asset cleanly with accessibility role and label", () => {
    const { getByLabelText } = render(<ProductAsset assetId="yara-hub-hero" size="md" />);
    expect(getByLabelText("تصویر هاب یارا")).toBeTruthy();
  });

  it("renders the marketplace hero banner asset with size=hero", () => {
    const { getByLabelText } = render(
      <ProductAsset assetId="yara-marketplace-hero" size="hero" resizeMode="cover" />
    );
    expect(getByLabelText("تصویر زیست‌بوم مراقبت سالمند یارا")).toBeTruthy();
  });

  it("renders all 12 assets without throwing errors", () => {
    for (const id of ALL_SEMANTIC_IDS) {
      const { root } = render(<ProductAsset assetId={id} size="sm" />);
      expect(root).toBeTruthy();
    }
  });
});
