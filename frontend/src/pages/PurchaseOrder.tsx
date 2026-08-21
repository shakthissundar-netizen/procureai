import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../components/ui';
import { api } from '../services/api';
import type { PurchaseOrder as POType } from '../types';
import { Printer, Download, CheckCircle2, Building2 } from 'lucide-react';

export function PurchaseOrder() {
  const [po, setPo] = useState<POType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Usually we would pass the Vendor ID from context/state, 
    // for this demo we'll fetch the recommendation and then generate PO for it
    api.getRecommendation('RFQ-2026-001').then(rec => {
      api.generatePO('RFQ-2026-001', rec.recommendedVendorId).then(data => {
        setPo(data);
        setLoading(false);
      });
    });
  }, []);

  if (loading || !po) {
    return <div className="flex h-full items-center justify-center"><div className="animate-pulse flex flex-col items-center"><div className="h-8 w-8 bg-primary-500 rounded-full mb-4"></div></div></div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex justify-between items-end">
        <div>
          <div className="flex items-center space-x-2 text-emerald-600 mb-1">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-semibold text-sm uppercase tracking-wider">Approved</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Purchase Order</h1>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            PDF
          </Button>
          <Button variant="outline">
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
        </div>
      </div>

      <Card className="bg-white shadow-sm border-slate-200 print:shadow-none print:border-none">
        <CardContent className="p-8 md:p-12">
          {/* Header */}
          <div className="flex justify-between items-start border-b border-slate-200 pb-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-primary-600 rounded-md flex items-center justify-center">
                  <span className="text-white font-bold text-lg leading-none">P</span>
                </div>
                <span className="font-bold tracking-tight text-xl text-slate-950">ProcureAI</span>
              </div>
              <p className="text-sm text-slate-500">123 Tech Park, Innovation Way</p>
              <p className="text-sm text-slate-500">Bangalore, India 560001</p>
              <p className="text-sm text-slate-500">finance@procureai.example.com</p>
            </div>
            <div className="text-right">
              <h2 className="text-3xl font-light text-slate-400 uppercase tracking-widest mb-4">Purchase Order</h2>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <span className="font-medium text-slate-500">PO Number:</span>
                <span className="font-bold text-slate-900">{po.poNumber}</span>
                <span className="font-medium text-slate-500">Date:</span>
                <span className="text-slate-900">{new Date(po.generatedAt).toLocaleDateString()}</span>
                <span className="font-medium text-slate-500">RFQ Ref:</span>
                <span className="text-slate-900">{po.rfqId}</span>
              </div>
            </div>
          </div>

          {/* Vendor Info */}
          <div className="mb-10">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Vendor Details</h3>
            <div className="flex items-start">
              <Building2 className="w-5 h-5 text-slate-400 mr-2 mt-0.5" />
              <div>
                <p className="font-bold text-slate-900">{po.vendorName}</p>
                <p className="text-sm text-slate-500">Vendor ID: V-10492</p>
                <p className="text-sm text-slate-500">Terms: {po.paymentTerms}</p>
                <p className="text-sm text-slate-500">Delivery: {po.deliveryTerms}</p>
              </div>
            </div>
          </div>

          {/* Line Items */}
          <table className="w-full text-sm mb-8">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="text-left py-3 font-semibold text-slate-900">Description</th>
                <th className="text-right py-3 font-semibold text-slate-900">Quantity</th>
                <th className="text-right py-3 font-semibold text-slate-900">Unit Price</th>
                <th className="text-right py-3 font-semibold text-slate-900">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="py-4 font-medium text-slate-900">{po.products}</td>
                <td className="py-4 text-right">{po.quantity}</td>
                <td className="py-4 text-right">₹{po.unitPrice.toLocaleString()}</td>
                <td className="py-4 text-right">₹{(po.unitPrice * po.quantity).toLocaleString()}</td>
              </tr>
            </tbody>
          </table>

          {/* Totals */}
          <div className="flex justify-end">
            <div className="w-64 space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Subtotal</span>
                <span className="font-medium text-slate-900">₹{(po.unitPrice * po.quantity).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Tax (18%)</span>
                <span className="font-medium text-slate-900">₹{po.taxAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between pt-3 border-t-2 border-slate-200">
                <span className="font-bold text-slate-900">Grand Total</span>
                <span className="font-bold text-lg text-primary-700">₹{po.totalAmount.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="mt-16 pt-8 border-t border-slate-200 text-sm text-slate-500 text-center">
            <p>This is a system generated purchase order based on AI recommendation and human approval.</p>
            <p>For terms and conditions, please refer to the master vendor agreement.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
