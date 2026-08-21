import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../components/ui';
import { api } from '../services/api';
import type { Recommendation as RecommendationType, VendorScore } from '../types';
import { CheckCircle, AlertTriangle, ShieldCheck, ThumbsUp } from 'lucide-react';

export function Recommendation() {
  const navigate = useNavigate();
  const [recommendation, setRecommendation] = useState<RecommendationType | null>(null);
  const [vendorScore, setVendorScore] = useState<VendorScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getRecommendation('RFQ-2026-001'),
      api.getScores('RFQ-2026-001')
    ]).then(([rec, scores]) => {
      setRecommendation(rec);
      const winner = scores.find(s => s.vendorId === rec.recommendedVendorId);
      if (winner) setVendorScore(winner);
      setLoading(false);
    });
  }, []);

  const handleApprove = () => {
    setApproving(true);
    setTimeout(() => {
      navigate('/po');
    }, 1000);
  };

  if (loading || !recommendation || !vendorScore) {
    return <div className="flex h-full items-center justify-center"><div className="animate-pulse flex flex-col items-center"><div className="h-8 w-8 bg-primary-500 rounded-full mb-4"></div></div></div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Final Recommendation</h1>
        <p className="text-slate-500 mt-1">Review the AI recommendation before approving the purchase order.</p>
      </div>

      <Card className="border-emerald-200 shadow-md">
        <div className="bg-emerald-50 px-6 py-8 flex flex-col items-center text-center border-b border-emerald-100">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-4">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <Badge variant="success" className="mb-2">AI Recommended Vendor</Badge>
          <h2 className="text-3xl font-bold text-slate-900">{recommendation.recommendedVendorId}</h2>
          <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
            <div className="flex flex-col items-center">
              <span className="text-slate-500">Final Score</span>
              <span className="text-xl font-bold text-emerald-700">{recommendation.finalScore} / 100</span>
            </div>
            <div className="w-px h-8 bg-emerald-200"></div>
            <div className="flex flex-col items-center">
              <span className="text-slate-500">Rank</span>
              <span className="text-xl font-bold text-emerald-700">#1</span>
            </div>
            <div className="w-px h-8 bg-emerald-200"></div>
            <div className="flex flex-col items-center">
              <span className="text-slate-500">Risk Level</span>
              <span className="text-xl font-bold text-emerald-700">Low</span>
            </div>
          </div>
        </div>
        <CardContent className="p-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-semibold text-slate-900 flex items-center mb-3">
                <CheckCircle className="w-5 h-5 text-emerald-500 mr-2" />
                Why this vendor?
              </h3>
              <ul className="space-y-2 pl-7">
                {recommendation.keyReasons.map((reason, i) => (
                  <li key={i} className="text-slate-700 text-sm list-disc">{reason}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-base font-semibold text-slate-900 flex items-center mb-3">
                <AlertTriangle className="w-5 h-5 text-amber-500 mr-2" />
                Trade-offs & Risks
              </h3>
              <ul className="space-y-2 pl-7">
                {recommendation.tradeOffs.map((tradeoff, i) => (
                  <li key={i} className="text-slate-700 text-sm list-disc">{tradeoff}</li>
                ))}
                {recommendation.detectedRisks.map((risk, i) => (
                  <li key={i + 'risk'} className="text-slate-700 text-sm list-disc">{risk}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end space-x-4">
        <Button variant="outline" onClick={() => navigate('/rfq/compare')}>Back to Comparison</Button>
        <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={handleApprove} disabled={approving}>
          {approving ? (
            'Generating PO...'
          ) : (
            <>
              <ThumbsUp className="w-5 h-5 mr-2" />
              Approve & Generate PO
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
