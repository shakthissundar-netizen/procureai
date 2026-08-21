import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../components/ui';
import { api } from '../services/api';
import type { VendorScore } from '../types';
import { AlertCircle, CheckCircle2, ChevronRight, AlertTriangle } from 'lucide-react';

export function VendorComparison() {
  const navigate = useNavigate();
  const [scores, setScores] = useState<VendorScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getScores('RFQ-2026-001').then(data => {
      // Sort by rank
      setScores(data.sort((a, b) => a.rank - b.rank));
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="flex h-full items-center justify-center"><div className="animate-pulse flex flex-col items-center"><div className="h-8 w-8 bg-primary-500 rounded-full mb-4"></div><p className="text-slate-500">Loading comparison...</p></div></div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Vendor Comparison</h1>
          <p className="text-slate-500 mt-1">AI-generated ranking based on your configured weights.</p>
        </div>
        <Button onClick={() => navigate('/rfq/trace')}>
          View AI Decision Trace <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-semibold">Rank</th>
                <th className="px-6 py-4 font-semibold">Vendor</th>
                <th className="px-6 py-4 font-semibold">Score</th>
                <th className="px-6 py-4 font-semibold">Price Component</th>
                <th className="px-6 py-4 font-semibold">Delivery Component</th>
                <th className="px-6 py-4 font-semibold">Warranty</th>
                <th className="px-6 py-4 font-semibold">Risk & Anomalies</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((vendor, index) => {
                const isWinner = index === 0;
                const hasAnomalies = vendor.anomalies.length > 0;
                
                return (
                  <tr key={vendor.vendorId} className={`border-b border-slate-100 hover:bg-slate-50 transition-colors ${isWinner ? 'bg-blue-50/30' : ''}`}>
                    <td className="px-6 py-4">
                      {isWinner ? (
                        <div className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center font-bold">1</div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold">{vendor.rank}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-900">
                      {vendor.vendorName}
                      {isWinner && <Badge variant="success" className="ml-2">Recommended</Badge>}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <span className="text-lg font-bold mr-2">{vendor.totalScore}</span>
                        <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${isWinner ? 'bg-primary-600' : 'bg-slate-400'}`} 
                            style={{ width: `${vendor.totalScore}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {vendor.components.price} / 30
                    </td>
                    <td className="px-6 py-4">
                      {vendor.components.delivery} / 25
                      {vendor.components.delivery < 10 && (
                        <AlertTriangle className="w-4 h-4 text-red-500 inline ml-2" />
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {vendor.components.warranty} / 10
                    </td>
                    <td className="px-6 py-4">
                      {hasAnomalies ? (
                        <div className="flex flex-col space-y-1">
                          {vendor.anomalies.map(anomaly => (
                            <div key={anomaly.id} className="flex items-start text-red-600 text-xs bg-red-50 p-1.5 rounded">
                              <AlertCircle className="w-3 h-3 mr-1 mt-0.5 shrink-0" />
                              <span title={anomaly.description}>{anomaly.type.replace('_', ' ')}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center text-emerald-600 text-xs">
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          No issues detected
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start text-blue-800">
        <AlertCircle className="w-5 h-5 mr-3 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-sm">Why isn't the cheapest vendor recommended?</h4>
          <p className="text-sm mt-1 opacity-90">
            Vendor B offers the lowest unit price, but our AI detected a <strong>Critical Delivery Violation</strong> and a <strong>Pricing Mismatch</strong> in their quotation. 
            Vendor C provides the best balance of price and reliability according to your 30% / 25% weight configuration.
          </p>
        </div>
      </div>
    </div>
  );
}
