import type { RFQ, Quotation, VendorScore, Recommendation, PurchaseOrder } from '../types';

export const mockRFQ: RFQ = {
  id: 'RFQ-2026-001',
  title: '500 Business Laptops',
  product: 'Business Laptop',
  quantity: 500,
  description: 'High-performance laptops for engineering and product teams.',
  targetUnitPrice: 50000,
  maxDeliveryDays: 15,
  minWarrantyYears: 3,
  requirements: [
    { id: 'r1', category: 'Quality', description: 'Intel i7 or equivalent', isMandatory: true },
    { id: 'r2', category: 'Quality', description: 'RAM >= 16 GB', isMandatory: true },
    { id: 'r3', category: 'Quality', description: 'Storage >= 512 GB SSD', isMandatory: true },
    { id: 'r4', category: 'Warranty', description: 'Warranty >= 3 years', targetValue: 3, unit: 'years', isMandatory: true },
    { id: 'r5', category: 'Delivery', description: 'Delivery <= 15 days', targetValue: 15, unit: 'days', isMandatory: true },
  ],
  weights: {
    price: 30,
    delivery: 25,
    quality: 20,
    warranty: 10,
    payment: 10,
    compliance: 5,
  },
  status: 'Completed',
  createdAt: new Date().toISOString(),
};

export const mockQuotations: Quotation[] = [
  {
    id: 'Q-001',
    vendorName: 'Vendor A (Reliable Tech)',
    quotationNumber: 'QT-2026-A1',
    productName: 'ProBook 7000',
    quantity: 500,
    unitPrice: 52000,
    deliveryDays: 10,
    warrantyYears: 3,
    paymentTerms: '30-day payment',
    taxPercentage: 18,
    additionalCharges: 0,
    grandTotal: 52000 * 500 * 1.18,
    status: 'Analyzed',
  },
  {
    id: 'Q-002',
    vendorName: 'Vendor B (Discount IT)',
    quotationNumber: 'QT-2026-B2',
    productName: 'ValueBook Pro',
    quantity: 500,
    unitPrice: 48500,
    deliveryDays: 25,
    warrantyYears: 5,
    paymentTerms: '15-day payment',
    taxPercentage: 18,
    additionalCharges: 50000,
    grandTotal: 48500 * 500 * 1.18, // Intentionally leaving out additional charges to simulate mismatch
    status: 'Analyzed',
  },
  {
    id: 'Q-003',
    vendorName: 'Vendor C (Balanced Solutions)',
    quotationNumber: 'QT-2026-C3',
    productName: 'OptiLap Enterprise',
    quantity: 500,
    unitPrice: 49800,
    deliveryDays: 12,
    warrantyYears: 3,
    paymentTerms: '45-day payment',
    taxPercentage: 18,
    additionalCharges: 0,
    grandTotal: 49800 * 500 * 1.18,
    status: 'Analyzed',
  }
];

export const mockScores: VendorScore[] = [
  {
    vendorId: 'Vendor C (Balanced Solutions)',
    vendorName: 'Vendor C (Balanced Solutions)',
    quotationId: 'Q-003',
    components: {
      price: 28, // Out of 30
      delivery: 22, // Out of 25
      quality: 18,
      warranty: 8,
      payment: 9,
      compliance: 5,
    },
    totalScore: 90,
    rank: 1,
    anomalies: [],
    requirementMatches: [
      { requirementId: 'r4', requirementDescription: 'Warranty >= 3 years', satisfied: true, vendorValue: '3 years' },
      { requirementId: 'r5', requirementDescription: 'Delivery <= 15 days', satisfied: true, vendorValue: '12 days' },
    ]
  },
  {
    vendorId: 'Vendor A (Reliable Tech)',
    vendorName: 'Vendor A (Reliable Tech)',
    quotationId: 'Q-001',
    components: {
      price: 24,
      delivery: 25,
      quality: 18,
      warranty: 8,
      payment: 7,
      compliance: 5,
    },
    totalScore: 87,
    rank: 2,
    anomalies: [],
    requirementMatches: [
      { requirementId: 'r4', requirementDescription: 'Warranty >= 3 years', satisfied: true, vendorValue: '3 years' },
      { requirementId: 'r5', requirementDescription: 'Delivery <= 15 days', satisfied: true, vendorValue: '10 days' },
    ]
  },
  {
    vendorId: 'Vendor B (Discount IT)',
    vendorName: 'Vendor B (Discount IT)',
    quotationId: 'Q-002',
    components: {
      price: 30,
      delivery: 5, // Penalized for violation
      quality: 18,
      warranty: 10,
      payment: 6,
      compliance: 3,
    },
    totalScore: 72,
    rank: 3,
    anomalies: [
      {
        id: 'A-001',
        type: 'DELIVERY_VIOLATION',
        severity: 'CRITICAL',
        description: 'Vendor delivery (25 days) exceeds requirement (<= 15 days)',
        field: 'deliveryDays'
      },
      {
        id: 'A-002',
        type: 'PRICE_MISMATCH',
        severity: 'WARNING',
        description: 'Grand total mismatch due to uncalculated additional charges',
        field: 'grandTotal'
      }
    ],
    requirementMatches: [
      { requirementId: 'r4', requirementDescription: 'Warranty >= 3 years', satisfied: true, vendorValue: '5 years' },
      { requirementId: 'r5', requirementDescription: 'Delivery <= 15 days', satisfied: false, vendorValue: '25 days' },
    ]
  }
];

export const mockRecommendation: Recommendation = {
  rfqId: 'RFQ-2026-001',
  recommendedVendorId: 'Vendor C (Balanced Solutions)',
  finalScore: 90,
  keyReasons: [
    'Provides the best overall trade-off between price and delivery.',
    'Meets all mandatory RFQ requirements including the 15-day delivery window.',
    'Favorable 45-day payment terms compared to competitors.',
  ],
  detectedRisks: [
    'No critical anomalies detected for this vendor.',
  ],
  tradeOffs: [
    'Slightly more expensive than Vendor B (₹1,300 premium per unit), but guarantees timely delivery.',
    'Delivery is 2 days slower than Vendor A, but yields significant cost savings (₹2,200 per unit).'
  ]
};

export const mockDashboardStats = {
  totalValue: '₹24.9M',
  activeRFQs: 12,
  quotesAnalyzed: 45,
  potentialSavings: '₹1.1M',
  anomaliesDetected: 8,
  recentActivity: [
    { id: 1, action: 'RFQ Created', details: '500 Business Laptops', time: '2 hours ago' },
    { id: 2, action: 'Quotation Uploaded', details: 'Vendor B - Laptops', time: '4 hours ago' },
    { id: 3, action: 'Analysis Completed', details: 'Office Furniture RFQ', time: '1 day ago' },
  ]
};
