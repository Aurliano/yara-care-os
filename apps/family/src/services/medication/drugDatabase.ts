export type DrugForm =
  | "tablet"
  | "capsule"
  | "syrup"
  | "drops"
  | "injection"
  | "ointment"
  | "inhaler"
  | "other";

export interface DrugItem {
  id: string;
  nameFa: string;
  nameEn: string;
  categoryFa: string;
  defaultForm: DrugForm;
  commonDosages: string[];
  defaultInstructionFa: string;
}

export const DRUG_FORMS: { id: DrugForm; labelFa: string; defaultUnitFa: string }[] = [
  { id: "tablet", labelFa: "قرص", defaultUnitFa: "عدد" },
  { id: "capsule", labelFa: "کپسول", defaultUnitFa: "عدد" },
  { id: "syrup", labelFa: "شربت", defaultUnitFa: "سی‌سی (قاشق)" },
  { id: "drops", labelFa: "قطره", defaultUnitFa: "قطره" },
  { id: "injection", labelFa: "آمپول / انسولین", defaultUnitFa: "واحد / نوبت" },
  { id: "inhaler", labelFa: "اسپری", defaultUnitFa: "پاف" },
  { id: "ointment", labelFa: "پماد / لوسیون", defaultUnitFa: "مرتبه" },
  { id: "other", labelFa: "سایر", defaultUnitFa: "نوبت" },
];

export const COMMON_DRUGS: DrugItem[] = [
  // قلب و عروق و فشار خون
  {
    id: "losartan",
    nameFa: "لوزارتان",
    nameEn: "Losartan",
    categoryFa: "فشار خون و قلب",
    defaultForm: "tablet",
    commonDosages: ["۲۵ میلی‌گرم", "۵۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "همراه با یک لیوان آب",
  },
  {
    id: "aspirin",
    nameFa: "آسپرین (آ.اس.آ)",
    nameEn: "Aspirin (ASA)",
    categoryFa: "قلب و عروق",
    defaultForm: "tablet",
    commonDosages: ["۸۰ میلی‌گرم", "۱۰۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "بعد از غذا",
  },
  {
    id: "atorvastatin",
    nameFa: "آتورواستاتین",
    nameEn: "Atorvastatin",
    categoryFa: "چربی خون",
    defaultForm: "tablet",
    commonDosages: ["۱۰ میلی‌گرم", "۲۰ میلی‌گرم", "۴۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "شب‌ها بعد از شام",
  },
  {
    id: "amlodipine",
    nameFa: "آملودیپین",
    nameEn: "Amlodipine",
    categoryFa: "فشار خون",
    defaultForm: "tablet",
    commonDosages: ["۵ میلی‌گرم", "۱۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "صبح‌ها قبل یا بعد از غذا",
  },
  {
    id: "metoprolol",
    nameFa: "متورال (متوپرولول)",
    nameEn: "Metoprolol (Metoral)",
    categoryFa: "قلب و ضربان",
    defaultForm: "tablet",
    commonDosages: ["۵۰ میلی‌گرم", "۱/۲ قرص", "۱ قرص"],
    defaultInstructionFa: "همراه با غذا",
  },
  {
    id: "propranolol",
    nameFa: "پروپرانولول (پرانول)",
    nameEn: "Propranolol",
    categoryFa: "قلب و اضطراب",
    defaultForm: "tablet",
    commonDosages: ["۱۰ میلی‌گرم", "۲۰ میلی‌گرم", "۴۰ میلی‌گرم"],
    defaultInstructionFa: "قبل از وعده غذایی",
  },
  {
    id: "digoxin",
    nameFa: "دیگوکسین",
    nameEn: "Digoxin",
    categoryFa: "نارسایی قلبی",
    defaultForm: "tablet",
    commonDosages: ["۰.۲۵ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "ساعت معین و منظم",
  },
  {
    id: "warfarin",
    nameFa: "وارفارین",
    nameEn: "Warfarin",
    categoryFa: "ضد انعقاد خون",
    defaultForm: "tablet",
    commonDosages: ["۵ میلی‌گرم", "۱/۲ قرص", "۱ قرص"],
    defaultInstructionFa: "عصرها در ساعت مشخص",
  },
  {
    id: "plavix",
    nameFa: "پلاویکس (کلوپیدوگرل)",
    nameEn: "Plavix (Clopidogrel)",
    categoryFa: "قلب و عروق",
    defaultForm: "tablet",
    commonDosages: ["۷۵ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "همراه با غذا یا بدون غذا",
  },
  {
    id: "captopril",
    nameFa: "کاپتوپریل",
    nameEn: "Captopril",
    categoryFa: "فشار خون",
    defaultForm: "tablet",
    commonDosages: ["۲۵ میلی‌گرم", "۵۰ میلی‌گرم"],
    defaultInstructionFa: "۱ ساعت قبل از غذا",
  },
  {
    id: "hydrochlorothiazide",
    nameFa: "هیدروکلروتیازید",
    nameEn: "Hydrochlorothiazide",
    categoryFa: "فشار خون و ادرارآور",
    defaultForm: "tablet",
    commonDosages: ["۵۰ میلی‌گرم", "۱/۲ قرص", "۱ عدد"],
    defaultInstructionFa: "صبح‌ها",
  },

  // دیابت و قند خون
  {
    id: "metformin",
    nameFa: "متفورمین",
    nameEn: "Metformin",
    categoryFa: "دیابت و قند خون",
    defaultForm: "tablet",
    commonDosages: ["۵۰۰ میلی‌گرم", "۱۰۰۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "همراه با غذا یا بلافاصله بعد از غذا",
  },
  {
    id: "glibenclamide",
    nameFa: "گلی‌بن‌کلامید",
    nameEn: "Glibenclamide",
    categoryFa: "دیابت و قند خون",
    defaultForm: "tablet",
    commonDosages: ["۵ میلی‌گرم", "۱/۲ قرص", "۱ قرص"],
    defaultInstructionFa: "۳۰ دقیقه قبل از غذا",
  },
  {
    id: "insulin_lantus",
    nameFa: "انسولین لانتوس (قلم خاکستری)",
    nameEn: "Insulin Lantus",
    categoryFa: "دیابت و انسولین",
    defaultForm: "injection",
    commonDosages: ["۱۰ واحد", "۱۵ واحد", "۲۰ واحد", "۲۴ واحد"],
    defaultInstructionFa: "شب‌ها سر ساعت مشخص تزریق شود",
  },
  {
    id: "insulin_novorapid",
    nameFa: "انسولین نوورپید (قلم نارنجی)",
    nameEn: "Insulin NovoRapid",
    categoryFa: "دیابت و انسولین",
    defaultForm: "injection",
    commonDosages: ["۴ واحد", "۶ واحد", "۸ واحد", "۱۰ واحد"],
    defaultInstructionFa: "بلافاصله قبل از وعده غذایی",
  },

  // مکمل‌ها و املاح
  {
    id: "calcium_d",
    nameFa: "کلسیم دی (Calcium D)",
    nameEn: "Calcium D",
    categoryFa: "مکمل و استخوان",
    defaultForm: "tablet",
    commonDosages: ["۱ عدد", "۲ عدد", "۵۰۰ میلی‌گرم"],
    defaultInstructionFa: "بعد از غذا با آب فراوان",
  },
  {
    id: "vitamin_d3",
    nameFa: "ویتامین دی ۳ (D3)",
    nameEn: "Vitamin D3",
    categoryFa: "مکمل و ویتامین",
    defaultForm: "capsule",
    commonDosages: ["۵۰,۰۰۰ واحد (هفتگی/ماهانه)", "۱۰۰۰ واحد روزانه"],
    defaultInstructionFa: "همراه با وعده غذایی چرب",
  },
  {
    id: "ferrous_sulfate",
    nameFa: "قرص آهن (فروس سولفات)",
    nameEn: "Ferrous Sulfate",
    categoryFa: "مکمل و کم‌خونی",
    defaultForm: "tablet",
    commonDosages: ["۱ عدد", "شبی ۱ عدد"],
    defaultInstructionFa: "با معده خالی یا همراه آب‌میوه طبیعی",
  },
  {
    id: "folic_acid",
    nameFa: "اسید فولیک",
    nameEn: "Folic Acid",
    categoryFa: "مکمل و ویتامین",
    defaultForm: "tablet",
    commonDosages: ["۱ میلی‌گرم", "۵ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "یک بار در روز",
  },
  {
    id: "vitamin_b_complex",
    nameFa: "ب کمپلکس (B-Complex)",
    nameEn: "Vitamin B-Complex",
    categoryFa: "مکمل و ویتامین",
    defaultForm: "tablet",
    commonDosages: ["۱ عدد"],
    defaultInstructionFa: "همراه با صبحانه",
  },

  // گوارش و معده
  {
    id: "omeprazole",
    nameFa: "امپرازول",
    nameEn: "Omeprazole",
    categoryFa: "معده و گوارش",
    defaultForm: "capsule",
    commonDosages: ["۲۰ میلی‌گرم", "۴۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "صبح‌ها ناشتا نیم ساعت قبل از صبحانه",
  },
  {
    id: "pantoprazole",
    nameFa: "پنتوپرازول",
    nameEn: "Pantoprazole",
    categoryFa: "معده و گوارش",
    defaultForm: "tablet",
    commonDosages: ["۲۰ میلی‌گرم", "۴۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "صبح‌ها ناشتا نیم ساعت قبل از صبحانه",
  },
  {
    id: "famotidine",
    nameFa: "فاموتیدین",
    nameEn: "Famotidine",
    categoryFa: "معده و رفلاکس",
    defaultForm: "tablet",
    commonDosages: ["۲۰ میلی‌گرم", "۴۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "شب‌ها قبل از خواب",
  },
  {
    id: "dimenhydrinate",
    nameFa: "دیمن هیدرینات",
    nameEn: "Dimenhydrinate",
    categoryFa: "سرگیجه و تهوع",
    defaultForm: "tablet",
    commonDosages: ["۵۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "نیم ساعت قبل از حرکت یا هنگام احساس تهوع",
  },
  {
    id: "lactulose",
    nameFa: "لاکتولوز (شربت ملین)",
    nameEn: "Lactulose",
    categoryFa: "گوارش و یبوست",
    defaultForm: "syrup",
    commonDosages: ["۱۰ سی‌سی", "۱۵ سی‌سی", "۱ قاشق غذاخوری"],
    defaultInstructionFa: "همراه با آب فراوان",
  },

  // تیرویید
  {
    id: "levothyroxine",
    nameFa: "لووتیروکسین (تیروئید)",
    nameEn: "Levothyroxine",
    categoryFa: "غدد و تیروئید",
    defaultForm: "tablet",
    commonDosages: ["۵۰ میکروگرم", "۱۰۰ میکروگرم", "۱/۲ قرص", "۱ عدد"],
    defaultInstructionFa: "حتماً صبح ناشتا حداقل نیم ساعت قبل از صبحانه",
  },

  // مسکن‌ها و استخوان
  {
    id: "acetaminophen",
    nameFa: "استامینوفن",
    nameEn: "Acetaminophen",
    categoryFa: "مسکن و تب‌بر",
    defaultForm: "tablet",
    commonDosages: ["۳۲۵ میلی‌گرم", "۵۰۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "در صورت احساس درد با آب",
  },
  {
    id: "gelofen",
    nameFa: "ژلوفن (ایبوپروفن ژلاتینی)",
    nameEn: "Gelofen (Ibuprofen)",
    categoryFa: "مسکن و التهاب",
    defaultForm: "capsule",
    commonDosages: ["۴۰۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "حتماً بعد از غذا با یک لیوان آب",
  },
  {
    id: "naproxen",
    nameFa: "ناپروکسن",
    nameEn: "Naproxen",
    categoryFa: "مسکن مفاصل",
    defaultForm: "tablet",
    commonDosages: ["۲۵۰ میلی‌گرم", "۵۰۰ میلی‌گرم", "۱ عدد"],
    defaultInstructionFa: "بعد از غذا",
  },
  {
    id: "baclofen",
    nameFa: "باکلوفن",
    nameEn: "Baclofen",
    categoryFa: "گرفتگی عضلانی",
    defaultForm: "tablet",
    commonDosages: ["۱۰ میلی‌گرم", "۲۵ میلی‌گرم"],
    defaultInstructionFa: "همراه با وعده غذایی",
  },

  // تنفسی و ریه
  {
    id: "salbutamol",
    nameFa: "سالبوتامول (اسپری آبی)",
    nameEn: "Salbutamol",
    categoryFa: "تنفسی و آسم",
    defaultForm: "inhaler",
    commonDosages: ["۲ پاف", "۱ پاف"],
    defaultInstructionFa: "هنگام تنگی نفس استنشاق شود",
  },
  {
    id: "seretide",
    nameFa: "سرتاید (اسپری بنفش)",
    nameEn: "Seretide",
    categoryFa: "تنفسی و آسم",
    defaultForm: "inhaler",
    commonDosages: ["۱ پاف", "۲ پاف"],
    defaultInstructionFa: "صبح و شب، بعد از مصرف دهان شسته شود",
  },

  // اعصاب و خواب
  {
    id: "gabapentin",
    nameFa: "گاباپنتین",
    nameEn: "Gabapentin",
    categoryFa: "اعصاب و دردهای عصبی",
    defaultForm: "capsule",
    commonDosages: ["۱۰۰ میلی‌گرم", "۳۰۰ میلی‌گرم"],
    defaultInstructionFa: "شب‌ها همراه با آب",
  },
  {
    id: "sertraline",
    nameFa: "سرترالین (آسنترا)",
    nameEn: "Sertraline (Asentra)",
    categoryFa: "اعصاب و روان",
    defaultForm: "tablet",
    commonDosages: ["۵۰ میلی‌گرم", "۱۰۰ میلی‌گرم"],
    defaultInstructionFa: "صبح‌ها یا شب‌ها سر ساعت معین",
  },
  {
    id: "alprazolam",
    nameFa: "آلپرازولام",
    nameEn: "Alprazolam",
    categoryFa: "خواب و آرام‌بخش",
    defaultForm: "tablet",
    commonDosages: ["۰.۵ میلی‌گرم", "۱/۲ قرص", "۱ قرص"],
    defaultInstructionFa: "قبل از خواب",
  },
  {
    id: "clonazepam",
    nameFa: "کلونازپام",
    nameEn: "Clonazepam",
    categoryFa: "آرام‌بخش و تشنج",
    defaultForm: "tablet",
    commonDosages: ["۱ میلی‌گرم", "۲ میلی‌گرم", "۱/۲ قرص"],
    defaultInstructionFa: "شب‌ها قبل از خواب",
  },

  // چشم
  {
    id: "artificial_tears",
    nameFa: "اشک مصنوعی",
    nameEn: "Artificial Tears",
    categoryFa: "چشم و بینایی",
    defaultForm: "drops",
    commonDosages: ["۱ قطره در هر چشم", "۲ قطره"],
    defaultInstructionFa: "هر ۶ تا ۸ ساعت",
  },
  {
    id: "timolol",
    nameFa: "تیمولول (قطره گلوکوم)",
    nameEn: "Timolol",
    categoryFa: "فشار چشم",
    defaultForm: "drops",
    commonDosages: ["۱ قطره در چشم مبتلا"],
    defaultInstructionFa: "صبح و شب سروقت",
  },
];

export function searchDrugs(query: string): DrugItem[] {
  const q = query.trim().toLowerCase();
  if (!q) return COMMON_DRUGS.slice(0, 8);
  return COMMON_DRUGS.filter(
    (d) =>
      d.nameFa.toLowerCase().includes(q) ||
      d.nameEn.toLowerCase().includes(q) ||
      d.categoryFa.toLowerCase().includes(q)
  );
}

