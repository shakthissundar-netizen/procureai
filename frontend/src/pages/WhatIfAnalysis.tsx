import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button } from '../components/ui';
import { api } from '../services/api';
import { Sliders, RefreshCw, ChevronRight, ArrowRight } from 'lucide-react';
import type { VendorScore } from '../types';

export function WhatIfAnalysis() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [originalScores, setOriginalScores] = useState<VendorScore[]>([]);
  const [currentScores, setCurrentScores] = useState<VendorScore[]>([]);
  
  const [weights, setWeights] = useState({
    price: 30,
    delivery: 25,
    quality: 20,
    warranty: 10,
    payment: 10,
    compliance: 5,
  });

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

  useEffect(() => {
    api.getScores('RFQ-2026-001').then(data => {
      const sorted = data.sort((a, b) => a.rank - b.rank);
      setOriginalScores(sorted);
      setCurrentScores(sorted);
      setLoading(false);
    });
  }, []);

  const updateWeight = (key: keyof typeof weights, value: number) => {
    setWeights(prev => ({ ...prev, [key]: value }));
  };

  const handleRecalculate = async () => {
    if (totalWeight !== 100) return;
    
    setRecalculating(true);
    const newScores = await api.recalculateScores('RFQ-2026-001', weights);
    setCurrentScores(newScores);
    setRecalculating(false);
  };

  if (loading) {
    return <div className="flex h-full items-center justify-center"><div className="animate-pulse flex flex-col items-center"><div className="h-8 w-8 bg-primary-500 rounded-full mb-4"></div></div></div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">What-If Analysis</h1>
          <p className="text-slate-500 mt-1">Adjust scoring weights to see how it affects vendor ranking.</p>
        </div>
        <Button onClick={() => navigate('/rfq/recommendation')}>
          Proceed to Recommendation <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls */}
        <Card className="lg:col-span-5">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center"><Sliders className="w-5 h-5 mr-2 text-primary-500" /> Adjust Weights</span>
              <span className={`text-sm font-bold ${totalWeight === 100 ? 'text-green-600' : 'text-red-500'}`}>
                Total: {totalWeight}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-5">
              {Object.entries(weights).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-medium text-slate-700 capitalize">{key}</label>
                    <span className="text-sm font-bold text-slate-900">{value}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="100" 
                    value={value}
                    onChange={(e) => updateWeight(key as any, parseInt(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                  />
                </div>
              ))}
              
              <div className="pt-4 border-t border-slate-100 mt-6">
                <Button 
                  className="w-full" 
                  onClick={handleRecalculate} 
                  disabled={recalculating || totalWeight !== 100}
                >
                  {recalculating ? (
                    <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Recalculating...</>
                  ) : (
                    <><RefreshCw className="w-4 h-4 mr-2" /> Recalculate Rankings</>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results Comparison */}
        <div className="lg:col-span-7 space-y-6">
          <Card>
            <CardHeader className="bg-slate-50 border-b border-slate-100">
              <CardTitle>Rankings Overview</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between space-y-4 md:space-y-0">
                {/* Before */}
                <div className="flex-1">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Original (30% Price)</h4>
                  <div className="space-y-3">
                    {originalScores.map((score, i) => (
                      <div key={score.vendorId} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white">
                        <div className="flex items-center">
                          <span className="w-6 text-slate-400 font-bold">{i + 1}.</span>
                          <span className="font-medium text-sm text-slate-900 truncate max-w-[120px]">{score.vendorName.split('(')[0]}</span>
                        </div>
                        <span className="font-mono font-bold text-slate-700">{score.totalScore}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="px-4 flex justify-center text-slate-300 hidden md:block">
                  <ArrowRight className="w-8 h-8" />
                </div>

                {/* After */}
                <div className="flex-1 relative">
                  {recalculating && (
                    <div className="absolute inset-0 bg-white/60 backdrop-blur-[1px] z-10 flex items-center justify-center">
                      <RefreshCw className="w-6 h-6 text-primary-500 animate-spin" />
                    </div>
                  )}
                  <h4 className="text-xs font-bold text-primary-600 uppercase tracking-wider mb-4">Simulated Result</h4>
                  <div className="space-y-3">
                    {currentScores.map((score, i) => {
                      // Determine if rank changed
                      const origIndex = originalScores.findIndex(s => s.vendorId === score.vendorId);
                      const rankChanged = origIndex !== i;
                      const wentUp = origIndex > i;
                      
                      return (
                        <div key={score.vendorId} className={`flex items-center justify-between p-3 rounded-lg border ${rankChanged ? 'border-primary-300 bg-primary-50' : 'border-slate-200 bg-white'} transition-all duration-500`}>
                          <div className="flex items-center">
                            <span className="w-6 font-bold text-slate-400">{i + 1}.</span>
                            <span className="font-medium text-sm text-slate-900 truncate max-w-[120px]">{score.vendorName.split('(')[0]}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {rankChanged && (
                              <span className={`text-xs font-bold ${wentUp ? 'text-green-600' : 'text-red-500'}`}>
                                {wentUp ? '↑' : '↓'}
                              </span>
                            )}
                            <span className="font-mono font-bold text-slate-700">{score.totalScore}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <div className="bg-slate-100 rounded-lg p-4 text-sm text-slate-600">
            <strong>Hint:</strong> Try increasing the <strong>Price</strong> weight above 40%. The system will recalculate without needing an LLM call, and you'll see Vendor B overtake Vendor C despite their delivery violation.
          </div>
        </div>
      </div>
    </div>
  );
}
