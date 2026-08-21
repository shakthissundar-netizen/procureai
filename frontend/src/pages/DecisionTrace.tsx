import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../components/ui';
import { api } from '../services/api';
import { CheckCircle2, XCircle, ChevronRight, BrainCircuit, AlertTriangle, ArrowRight } from 'lucide-react';

export function DecisionTrace() {
  const navigate = useNavigate();
  const [recommendation, setRecommendation] = useState<any>(null);
  const [scores, setScores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getRecommendation('RFQ-2026-001'),
      api.getScores('RFQ-2026-001')
    ]).then(([recData, scoresData]) => {
      setRecommendation(recData);
      setScores(scoresData);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="flex h-full items-center justify-center"><div className="animate-pulse flex flex-col items-center"><div className="h-8 w-8 bg-primary-500 rounded-full mb-4"></div><p className="text-slate-500">Loading AI trace...</p></div></div>;
  }

  const winner = scores.find(s => s.vendorId === recommendation.recommendedVendorId);
  const others = scores.filter(s => s.vendorId !== recommendation.recommendedVendorId);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex justify-between items-end border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-primary-600 mb-1">
            <BrainCircuit className="w-5 h-5" />
            <span className="font-semibold text-sm uppercase tracking-wider">AI Decision Trace</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Why was {winner?.vendorName} recommended?</h1>
        </div>
        <Button onClick={() => navigate('/rfq/what-if')}>
          Try What-If Analysis <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Requirement Analysis */}
        <Card className="shadow-md border-slate-200">
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="text-lg">Requirement Analysis</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* Delivery Req */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 bg-slate-100 p-2 rounded mb-3 flex justify-between">
                  <span>Delivery</span>
                  <span className="font-bold text-slate-900">Required: &lt;= 15 days</span>
                </h4>
                <div className="space-y-2 pl-2">
                  <div className="flex justify-between items-center p-2 rounded bg-green-50 border border-green-100">
                    <span className="text-sm font-medium">{winner.vendorName}</span>
                    <div className="flex items-center">
                      <span className="font-bold text-slate-900 mr-2">12 days</span>
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded">
                    <span className="text-sm text-slate-600">Vendor A</span>
                    <div className="flex items-center">
                      <span className="text-sm text-slate-900 mr-2">10 days</span>
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded bg-red-50 border border-red-100">
                    <span className="text-sm text-slate-600">Vendor B</span>
                    <div className="flex items-center">
                      <span className="text-sm font-bold text-red-600 mr-2">25 days</span>
                      <XCircle className="w-4 h-4 text-red-600" />
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Warranty Req */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 bg-slate-100 p-2 rounded mb-3 flex justify-between">
                  <span>Warranty</span>
                  <span className="font-bold text-slate-900">Required: &gt;= 3 years</span>
                </h4>
                <div className="space-y-2 pl-2">
                  <div className="flex justify-between items-center p-2 rounded bg-green-50 border border-green-100">
                    <span className="text-sm font-medium">{winner.vendorName}</span>
                    <div className="flex items-center">
                      <span className="font-bold text-slate-900 mr-2">3 years</span>
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-2 rounded">
                    <span className="text-sm text-slate-600">Vendor B</span>
                    <div className="flex items-center">
                      <span className="text-sm text-slate-900 mr-2">5 years</span>
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {/* Price Analysis & Anomalies */}
          <Card className="shadow-md border-slate-200">
            <CardHeader className="bg-slate-50 border-b border-slate-100">
              <CardTitle className="text-lg">Price Analysis & Anomalies</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                  <span className="text-sm text-slate-600">Vendor A</span>
                  <span className="font-mono text-slate-900">₹52,000</span>
                </div>
                <div className="flex flex-col pb-2 border-b border-slate-100">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-slate-600">Vendor B</span>
                    <span className="font-mono font-bold text-green-600">₹48,500</span>
                  </div>
                  <div className="bg-red-50 p-2 rounded border border-red-100 text-xs text-red-700 flex items-start mt-2">
                    <AlertTriangle className="w-3 h-3 mr-1.5 mt-0.5 shrink-0" />
                    <div>
                      <strong>Anomaly Detected:</strong> Deliberate grand-total mismatch. Additional charges of ₹50,000 were hidden from the unit price total.
                    </div>
                  </div>
                </div>
                <div className="flex justify-between items-center bg-blue-50/50 p-2 rounded border border-blue-100">
                  <span className="text-sm font-bold text-primary-700">{winner.vendorName}</span>
                  <span className="font-mono font-bold text-primary-700">₹49,800</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Final Decision */}
          <Card className="bg-primary-900 text-white shadow-lg border-none overflow-hidden">
            <div className="absolute top-0 right-0 p-12 opacity-10 pointer-events-none">
              <BrainCircuit className="w-48 h-48" />
            </div>
            <CardContent className="pt-6 relative z-10">
              <Badge className="bg-primary-500 hover:bg-primary-500 mb-4 border-none">AI Recommendation</Badge>
              <h3 className="text-2xl font-bold mb-4">{winner.vendorName}</h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-primary-300 text-sm font-semibold mb-2 uppercase tracking-wide">Key Reasons</h4>
                  <ul className="space-y-2">
                    {recommendation.keyReasons.map((r: string, i: number) => (
                      <li key={i} className="flex items-start text-sm">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 mt-0.5 shrink-0" />
                        <span className="opacity-90">{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="pt-4 border-t border-primary-800">
                  <h4 className="text-primary-300 text-sm font-semibold mb-2 uppercase tracking-wide">Trade-offs Accepted</h4>
                  <ul className="space-y-2">
                    {recommendation.tradeOffs.map((t: string, i: number) => (
                      <li key={i} className="flex items-start text-sm">
                        <ArrowRight className="w-4 h-4 text-amber-400 mr-2 mt-0.5 shrink-0" />
                        <span className="opacity-90">{t}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
