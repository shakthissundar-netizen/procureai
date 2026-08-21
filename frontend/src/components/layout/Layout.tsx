import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Upload, 
  BarChart2, 
  GitMerge, 
  Sliders, 
  CheckCircle,
  FileCheck,
  Settings,
  Bell,
  Search
} from 'lucide-react';

export function Layout() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/rfq/create', label: 'Create RFQ', icon: FileText },
    { path: '/rfq/upload', label: 'Quotations', icon: Upload },
    { path: '/rfq/compare', label: 'Compare Vendors', icon: BarChart2 },
    { path: '/rfq/trace', label: 'AI Decision Trace', icon: GitMerge },
    { path: '/rfq/what-if', label: 'What-If Analysis', icon: Sliders },
    { path: '/rfq/recommendation', label: 'Recommendation', icon: CheckCircle },
    { path: '/po', label: 'Purchase Orders', icon: FileCheck },
  ];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col hidden md:flex shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <div className="w-8 h-8 bg-primary-600 rounded-md flex items-center justify-center mr-3">
            <span className="text-white font-bold text-lg leading-none">P</span>
          </div>
          <span className="font-bold tracking-tight text-xl text-slate-950">ProcureAI</span>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || 
                             (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive 
                    ? 'bg-primary-50 text-primary-700' 
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <item.icon className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive ? 'text-primary-700' : 'text-slate-400'}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        
        <div className="p-4 border-t border-slate-200">
          <Link to="#" className="flex items-center px-3 py-2 text-sm font-medium rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900">
            <Settings className="mr-3 h-5 w-5 text-slate-400" />
            Settings
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center bg-slate-100 rounded-md px-3 py-1.5 w-96 border border-transparent focus-within:border-primary-500 focus-within:bg-white transition-colors">
            <Search className="h-4 w-4 text-slate-400 mr-2" />
            <input 
              type="text" 
              placeholder="Search RFQs, Vendors, POs..." 
              className="bg-transparent border-none outline-none text-sm w-full placeholder:text-slate-500"
            />
          </div>
          
          <div className="flex items-center space-x-4">
            <button className="relative text-slate-500 hover:text-slate-700">
              <Bell className="h-5 w-5" />
              <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-500 ring-2 ring-white"></span>
            </button>
            <div className="h-8 w-8 rounded-full bg-primary-100 border border-primary-200 flex items-center justify-center text-primary-700 font-medium text-sm">
              JD
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-slate-50 p-6 md:p-8">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
