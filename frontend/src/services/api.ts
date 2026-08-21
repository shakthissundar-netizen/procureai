import type { RFQ, Quotation, VendorScore, Recommendation, PurchaseOrder } from '../types';
import { mockRFQ, mockQuotations, mockScores, mockRecommendation, mockDashboardStats } from './mockData';

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const api = {
  getDashboardStats: async () => {
    await delay(500);
    return mockDashboardStats;
  },

  getRFQ: async (id: string): Promise<RFQ> => {
    await delay(300);
    return mockRFQ;
  },

  createRFQ: async (data: Partial<RFQ>): Promise<RFQ> => {
    await delay(800);
    return { ...mockRFQ, ...data, id: 'RFQ-' + Date.now() } as RFQ;
  },

  getQuotations: async (rfqId: string): Promise<Quotation[]> => {
    await delay(600);
    return mockQuotations;
  },

  analyzeQuotations: async (rfqId: string): Promise<{ status: string }> => {
    // Simulate long analysis process
    await delay(3000);
    return { status: 'Success' };
  },

  getScores: async (rfqId: string): Promise<VendorScore[]> => {
    await delay(400);
    return mockScores;
  },

  recalculateScores: async (rfqId: string, weights: any): Promise<VendorScore[]> => {
    await delay(800);
    // Simple mock to shuffle scores a bit based on weight change
    // If price weight > 40, Vendor B wins. Otherwise Vendor C wins.
    const priceWeight = weights.price || 30;
    
    if (priceWeight >= 40) {
      return [...mockScores].sort((a, b) => a.vendorId === 'Vendor B (Discount IT)' ? -1 : 1).map((s, i) => ({...s, rank: i + 1}));
    }
    return mockScores; // Default mock returns C as 1st
  },

  getRecommendation: async (rfqId: string): Promise<Recommendation> => {
    await delay(500);
    return mockRecommendation;
  },

  generatePO: async (rfqId: string, vendorId: string): Promise<PurchaseOrder> => {
    await delay(1000);
    const vendor = mockQuotations.find(q => q.vendorName === vendorId);
    return {
      id: 'PO-2026-001',
      poNumber: 'PO-' + Date.now(),
      rfqId,
      vendorName: vendorId,
      products: vendor?.productName || 'Business Laptops',
      quantity: vendor?.quantity || 500,
      unitPrice: vendor?.unitPrice || 50000,
      taxAmount: (vendor?.unitPrice || 50000) * (vendor?.quantity || 500) * 0.18,
      totalAmount: vendor?.grandTotal || 25000000,
      deliveryTerms: vendor?.deliveryDays + ' days',
      paymentTerms: vendor?.paymentTerms || '30-day payment',
      status: 'Draft',
      generatedAt: new Date().toISOString()
    };
  }
};
