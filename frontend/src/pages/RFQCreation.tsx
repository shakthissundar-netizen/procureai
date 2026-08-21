import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button } from '../components/ui';
import { api } from '../services/api';
import { Save, Plus } from 'lucide-react';

export function RFQCreation() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [weights, setWeights] = useState({
    price: 30,
    delivery: 25,
    quality: 20,
    warranty: 10,
    payment: 10,
    compliance: 5,
  });

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Mock create call
    await api.createRFQ({ weights });
    setLoading(false);
    navigate('/rfq/upload');
  };

  const updateWeight = (key: keyof typeof weights, value: number) => {
    setWeights(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Create RFQ</h1>
        <p className="text-slate-500 mt-1">Define product requirements and AI scoring weights.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>General Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">RFQ Title</label>
                <input type="text" defaultValue="500 Business Laptops" className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500" required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Product Category</label>
                <input type="text" defaultValue="Hardware" className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500" required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Quantity</label>
                <input type="number" defaultValue={500} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500" required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Target Unit Price (₹)</label>
                <input type="number" defaultValue={50000} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500" required />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Description</label>
              <textarea rows={3} defaultValue="High-performance laptops for engineering and product teams." className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>Specific Requirements</span>
              <Button type="button" variant="outline" size="sm"><Plus className="w-4 h-4 mr-2" /> Add Requirement</Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                'Intel i7 or equivalent',
                'RAM >= 16 GB',
                'Storage >= 512 GB SSD',
                'Warranty >= 3 years',
                'Delivery <= 15 days'
              ].map((req, i) => (
                <div key={i} className="flex items-center space-x-3 bg-slate-50 p-3 rounded-md border border-slate-100">
                  <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">{i+1}</div>
                  <input type="text" defaultValue={req} className="flex-1 bg-transparent border-none focus:ring-0 text-sm font-medium text-slate-700" />
                  <div className="px-2 py-1 bg-slate-200 rounded text-xs text-slate-600 font-medium cursor-pointer">Mandatory</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>AI Scoring Weights</span>
              <span className={`text-sm font-bold ${totalWeight === 100 ? 'text-green-600' : 'text-red-500'}`}>
                Total: {totalWeight}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              {Object.entries(weights).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-medium text-slate-700 capitalize">{key}</label>
                    <span className="text-sm font-bold text-primary-600">{value}%</span>
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
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end space-x-4">
          <Button variant="outline" type="button">Cancel</Button>
          <Button type="submit" disabled={loading || totalWeight !== 100}>
            {loading ? 'Creating...' : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save & Proceed to Upload
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
