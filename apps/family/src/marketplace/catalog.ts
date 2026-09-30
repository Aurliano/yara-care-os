import type { ProductAssetId } from "./assets";
import type { IconKey } from "../ui/iconXml";
import { toPersianDigits } from "../i18n/numerals";

export type AcquisitionMethod = "buy" | "rent";
export type SubscriptionTier = "monthly" | "annual";
export type RentalDurationMonths = 1 | 3 | 6 | 12;

export interface PackageConfiguration {
  productId: string;
  method: AcquisitionMethod;
  subscriptionTier: SubscriptionTier;
  rentalDurationMonths: RentalDurationMonths;
}

export interface IncludedItem {
  name: string;
  icon: IconKey;
  count: number;
  description: string;
}

export interface MarketplaceProduct {
  id: "yara-hub" | "yara-care" | "yara-care-plus";
  name: string;
  tag: string;
  assetId: ProductAssetId;
  shortDescription: string;
  fullDescription: string;
  includedDevices: IncludedItem[];
  keyBenefits: string[];
  startingPrice: number;
  pricing: {
    purchasePrice: number;
    monthlySubscriptionPrice: number;
    annualSubscriptionPrice: number;
    rentalRates: Record<RentalDurationMonths, number>;
  };
}

export interface CalculatedPrice {
  method: AcquisitionMethod;
  amount: number;
  currency: "TOMAN";
  formattedPrice: string;
  modeLabel: string;
  periodLabel: string;
  billingNote: string;
  // Specific to BUY
  devicePrice?: number;
  formattedDevicePrice?: string;
  subscriptionPrice?: number;
  formattedSubscriptionPrice?: string;
  subscriptionTierLabel?: string;
  freeSubscriptionMonths?: number;
  freeSubscriptionBenefit?: string;
  initialPaymentAmount?: number;
  formattedInitialPayment?: string;
  // Specific to RENT
  rentalDurationMonths?: RentalDurationMonths;
}

export interface PricingProvider {
  calculatePrice(config: PackageConfiguration): CalculatedPrice;
}

export const PRODUCTS: MarketplaceProduct[] = [
  {
    id: "yara-hub",
    name: "هاب یارا",
    tag: "دستگاه رومیزی مستقل",
    assetId: "yara-hub",
    shortDescription: "دستگاه لمسی و صوتی ویژه خانه عزیز سالمند با رابط کاربری درشت، آرام و پایدار.",
    fullDescription:
      "هاب یارا همراه اختصاصی عزیز سالخورده در منزل است. این دستگاه بدون نیاز به تلفن همراه یا رمزهای عبور پیچیده، وظایف روزانه و یادآوری‌های دارویی را با هشدارهای صوتی و دیداری رسا اعلام می‌کند و ارتباط مستقیم با خانواده را فراهم می‌سازد.",
    includedDevices: [
      {
        name: "هاب رومیزی لمسی یارا",
        icon: "hub",
        count: 1,
        description: "صفحه‌نمایش اختصاصی با فونت بسیار خوانا و پایه رومیزی مقاوم",
      },
    ],
    keyBenefits: [
      "رابط کاربری بزرگ، آرام و بدون نیاز به سواد کار با گوشی هوشمند",
      "عملکرد پایدار و یادآوری آفلاین حتی هنگام قطعی اینترنت",
      "امکان برقراری تماس مستقیم و آسان با خانواده",
      "بلندگوی رسا و تنظیم خودکار روشنایی متناسب با شب و روز",
    ],
    startingPrice: 350000,
    pricing: {
      purchasePrice: 8900000,
      monthlySubscriptionPrice: 350000,
      annualSubscriptionPrice: 3500000,
      rentalRates: {
        1: 650000,
        3: 1800000,
        6: 3300000,
        12: 6000000,
      },
    },
  },
  {
    id: "yara-care",
    name: "بسته مراقبت یارا",
    tag: "هاب رومیزی + جعبه دارو",
    assetId: "yara-care",
    shortDescription: "شامل هاب لمسی یارا و جعبه داروی هوشمند متصل برای انضباط دقیق در مصرف داروها.",
    fullDescription:
      "بسته استاندارد مراقبت خانگی یارا که هاب رومیزی را با جعبه داروی هوشمند پیوند می‌دهد. هر زمان موعد مصرف دارو فرا برسد، هاب با صدا و تصویر ملایم یادآوری می‌کند و وضعیت باز شدن محفظه‌ها به صورت خودکار برای خانواده ثبت می‌شود.",
    includedDevices: [
      {
        name: "هاب رومیزی لمسی یارا",
        icon: "hub",
        count: 1,
        description: "دستگاه ارتباطی و یادآوری مرکزی در خانه",
      },
      {
        name: "جعبه داروی هوشمند یارا",
        icon: "pillbox",
        count: 1,
        description: "محفظه‌های زمان‌بندی‌شده با سنسور تشخیص مصرف دارو",
      },
    ],
    keyBenefits: [
      "هماهنگی خودکار جعبه دارو با هاب از طریق بلوتوث بدون نیاز به تنظیم کاربر",
      "سنسور تشخیص مصرف دارو و پیشگیری از دوز تکراری یا فراموشی",
      "اطلاع‌رسانی بلادرنگ به مراقبان خانواده در اپلیکیشن",
      "پایداری یادآوری‌های دارویی حتی در صورت عدم اتصال اینترنت",
    ],
    startingPrice: 550000,
    pricing: {
      purchasePrice: 13500000,
      monthlySubscriptionPrice: 550000,
      annualSubscriptionPrice: 5500000,
      rentalRates: {
        1: 950000,
        3: 2650000,
        6: 4900000,
        12: 8900000,
      },
    },
  },
  {
    id: "yara-care-plus",
    name: "بسته مراقبت پلاس",
    tag: "زیست‌بوم جامع سلامت و تحرک",
    assetId: "yara-care-plus",
    shortDescription: "کامل‌ترین بسته همراهی: هاب لمسی، جعبه داروی هوشمند و ابزار پوشیدنی سلامت.",
    fullDescription:
      "کامل‌ترین همراه مراقبت از راه دور یارا برای خانواده‌هایی که می‌خواهند از فعالیت، آسایش و ایمنی عزیزشان در تمام ساعات شبانه‌روز اطمینان داشته باشند. این بسته علاوه بر هاب و جعبه دارو، شامل پوشیدنی سبک سلامت با باتری بادوام است.",
    includedDevices: [
      {
        name: "هاب رومیزی لمسی یارا",
        icon: "hub",
        count: 1,
        description: "دستگاه اصلی ارتباط و اعلان‌های دیداری/صوتی",
      },
      {
        name: "جعبه داروی هوشمند یارا",
        icon: "pillbox",
        count: 1,
        description: "محفظه دارویی هوشمند با قفل ایمن و سنسور مصرف",
      },
      {
        name: "پوشیدنی سلامت و تحرک",
        icon: "walking",
        count: 1,
        description: "مچ‌بند سبک و ضدآب برای پایش ملایم تحرک و اعلام نیاز به کمک",
      },
    ],
    keyBenefits: [
      "دیده‌بانی آرامش‌بخش فعالیت و الگوی تحرک بدون حس نظارت تحمیلی",
      "کلید تماس آسان روی مچ‌بند جهت اعلام نیاز فوری به هاب",
      "طراحی ارگونومیک، ضدحساسیت و عمر باتری چندروزه",
      "پشتیبانی اولویت‌دار و گزارش‌های تجمیعی دوره‌ای برای خانواده",
    ],
    startingPrice: 790000,
    pricing: {
      purchasePrice: 18900000,
      monthlySubscriptionPrice: 790000,
      annualSubscriptionPrice: 7900000,
      rentalRates: {
        1: 1350000,
        3: 3800000,
        6: 7000000,
        12: 12800000,
      },
    },
  },
];

export function getProductById(id: string): MarketplaceProduct | undefined {
  return PRODUCTS.find((p) => p.id === id);
}

export function formatToman(amount: number): string {
  const formattedWithCommas = amount.toLocaleString("en-US");
  return `${toPersianDigits(formattedWithCommas)} تومان`;
}

/**
 * Local Presentation Pricing Provider for R1.1.
 *
 * Implements two distinct acquisition models:
 * 1. BUY: Hardware ownership + Yara service subscription + 3 months free subscription gift
 * 2. RENT: Time-limited device usage (1, 3, 6, 12 months) without purchase
 */
export class LocalPricingProvider implements PricingProvider {
  calculatePrice(config: PackageConfiguration): CalculatedPrice {
    const product = getProductById(config.productId) ?? PRODUCTS[0];
    const { method, subscriptionTier = "monthly", rentalDurationMonths = 1 } = config;

    if (method === "buy") {
      const devicePrice = product.pricing.purchasePrice;
      const isAnnual = subscriptionTier === "annual";
      const subscriptionPrice = isAnnual
        ? product.pricing.annualSubscriptionPrice
        : product.pricing.monthlySubscriptionPrice;
      const subscriptionTierLabel = isAnnual
        ? "اشتراک سالانه (با تخفیف)"
        : "اشتراک ماهانه";

      return {
        method: "buy",
        amount: devicePrice,
        currency: "TOMAN",
        formattedPrice: formatToman(devicePrice),
        modeLabel: "خرید دستگاه",
        periodLabel: "مالکیت قطعی دستگاه",
        billingNote: "مالکیت قطعی سخت‌افزار همراه با ۳ ماه اشتراک رایگان خدمات یارا",
        devicePrice,
        formattedDevicePrice: formatToman(devicePrice),
        subscriptionPrice,
        formattedSubscriptionPrice: formatToman(subscriptionPrice),
        subscriptionTierLabel,
        freeSubscriptionMonths: 3,
        freeSubscriptionBenefit: "۳ ماه اشتراک رایگان همراه خرید دستگاه",
        initialPaymentAmount: devicePrice,
        formattedInitialPayment: formatToman(devicePrice),
      };
    }

    // Rental model
    const duration = rentalDurationMonths in product.pricing.rentalRates ? rentalDurationMonths : 1;
    const amount = product.pricing.rentalRates[duration];
    return {
      method: "rent",
      amount,
      currency: "TOMAN",
      formattedPrice: formatToman(amount),
      modeLabel: `اجاره ${toPersianDigits(duration)} ماهه`,
      periodLabel: `مبلغ کل برای ${toPersianDigits(duration)} ماه اجاره`,
      billingNote: "استفاده از دستگاه برای مدت مشخص بدون خرید دستگاه، شامل گارانتی کامل و خدمات",
      rentalDurationMonths: duration,
    };
  }
}

export const defaultPricingProvider: PricingProvider = new LocalPricingProvider();
