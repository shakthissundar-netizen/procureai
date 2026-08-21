import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { api } from '../services/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from 'recharts';
import { DollarSign, FileText, CheckCircle, AlertTriangle, TrendingUp, Sparkles } from 'lucide-react';

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardStats().then(data => {
      setStats(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="flex h-full items-center justify-center"><div className="animate-pulse flex flex-col items-center"><div className="h-8 w-8 bg-primary-500 rounded-full mb-4"></div><p className="text-slate-500">Loading dashboard...</p></div></div>;
  }

  const savingsData = [
    { month: 'Jan', savings: 1.2 },
    { month: 'Feb', savings: 1.8 },
    { month: 'Mar', savings: 1.5 },
    { month: 'Apr', savings: 2.1 },
    { month: 'May', savings: 2.4 },
    { month: 'Jun', savings: 3.1 },
  ];

  const vendorPerformance = [
    { name: 'Vendor A', score: 87 },
    { name: 'Vendor B', score: 72 },
    { name: 'Vendor C', score: 90 },
    { name: 'Vendor D', score: 65 },
    { name: 'Vendor E', score: 81 },
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Overview of procurement activities and AI insights.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <div className="p-3 bg-blue-100 text-blue-700 rounded-full">
              <DollarSign className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Total Procurement Value</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats.totalValue}</h3>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <div className="p-3 bg-indigo-100 text-indigo-700 rounded-full">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Active RFQs</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats.activeRFQs}</h3>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <div className="p-3 bg-emerald-100 text-emerald-700 rounded-full">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Quotations Analyzed</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats.quotesAnalyzed}</h3>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center space-x-4">
            <div className="p-3 bg-amber-100 text-amber-700 rounded-full">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Anomalies Detected</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats.anomaliesDetected}</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 hidden lg:block">
          <CardContent className="p-6 flex items-center space-x-4">
            <div className="p-3 bg-green-100 text-green-700 rounded-full">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Potential Savings Identified</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats.potentialSavings}</h3>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Charts */}
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-primary-500" />
              Potential AI Savings (Millions ₹)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={savingsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val}M`} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Line type="monotone" dataKey="savings" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Vendor AI Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={vendorPerformance} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" domain={[0, 100]} hide />
                  <YAxis dataKey="name" type="category" width={80} stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {
                      vendorPerformance.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.score >= 85 ? '#10b981' : entry.score >= 75 ? '#3b82f6' : '#f59e0b'} />
                      ))
                    }
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Radar Chart — Vendor Performance by Category */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Top Vendor — Score Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={[
                  { category: 'Price', score: 28 },
                  { category: 'Delivery', score: 22 },
                  { category: 'Quality', score: 18 },
                  { category: 'Warranty', score: 8 },
                  { category: 'Payment', score: 9 },
                  { category: 'Compliance', score: 5 },
                ]}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <Radar name="Vendor C" dataKey="score" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.25} strokeWidth={2} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent AI Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recentActivity.map((activity: any) => (
                <div key={activity.id} className="flex items-center justify-between border-b border-slate-100 last:border-0 pb-4 last:pb-0">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 rounded-full bg-primary-500"></div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{activity.action}</p>
                      <p className="text-xs text-slate-500">{activity.details}</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-400">{activity.time}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
