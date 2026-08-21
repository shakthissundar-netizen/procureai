export interface RFQRequirement {
  id: string;
  category: 'Price' | 'Delivery' | 'Quality' | 'Warranty' | 'Payment' | 'Compliance';
  description: string;
  targetValue?: number;
  unit?: string;
  isMandatory: boolean;
}

export interface RFQ {
  id: string;
  title: string;
  product: string;
  quantity: number;
  description: string;
  targetUnitPrice: number;
  maxDeliveryDays: number;
  minWarrantyYears: number;
  requirements: RFQRequirement[];
  weights: {
    price: number;
    delivery: number;
    quality: number;
    warranty: number;
    payment: number;
    compliance: number;
  };
  status: 'Draft' | 'Active' | 'Analyzing' | 'Completed';
  createdAt: string;
}

export interface Quotation {
  id: string;
  vendorName: string;
  quotationNumber: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  deliveryDays: number;
  warrantyYears: number;
  paymentTerms: string;
  taxPercentage: number;
  additionalCharges: number;
  grandTotal: number;
  status: 'Pending' | 'Extracted' | 'Analyzed';
  fileUrl?: string;
}

export interface Anomaly {
  id: string;
  type: 'DELIVERY_VIOLATION' | 'WARRANTY_VIOLATION' | 'PRICE_MISMATCH' | 'TAX_INCONSISTENCY' | 'ADDITIONAL_CHARGES' | 'MISSING_FIELD' | 'SUSPICIOUS_PRICING';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  description: string;
  field?: string;
}

export interface RequirementMatch {
  requirementId: string;
  requirementDescription: string;
  satisfied: boolean;
  vendorValue: string | number;
}

export interface VendorScore {
  vendorId: string;
  vendorName: string;
  quotationId: string;
  components: {
    price: number;
    delivery: number;
    quality: number;
    warranty: number;
    payment: number;
    compliance: number;
  };
  totalScore: number;
  rank: number;
  anomalies: Anomaly[];
  requirementMatches: RequirementMatch[];
}

export interface Recommendation {
  rfqId: string;
  recommendedVendorId: string;
  finalScore: number;
  keyReasons: string[];
  detectedRisks: string[];
  tradeOffs: string[];
}

export interface PurchaseOrder {
  id: string;
  poNumber: string;
  rfqId: string;
  vendorName: string;
  products: string;
  quantity: number;
  unitPrice: number;
  taxAmount: number;
  totalAmount: number;
  deliveryTerms: string;
  paymentTerms: string;
  status: 'Draft' | 'Approved' | 'Sent';
  generatedAt: string;
}
