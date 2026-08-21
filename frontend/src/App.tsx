
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { RFQCreation } from './pages/RFQCreation';
import { QuotationUpload } from './pages/QuotationUpload';
import { VendorComparison } from './pages/VendorComparison';
import { DecisionTrace } from './pages/DecisionTrace';
import { WhatIfAnalysis } from './pages/WhatIfAnalysis';
import { Recommendation } from './pages/Recommendation';
import { PurchaseOrder } from './pages/PurchaseOrder';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="rfq/create" element={<RFQCreation />} />
          <Route path="rfq/upload" element={<QuotationUpload />} />
          <Route path="rfq/compare" element={<VendorComparison />} />
          <Route path="rfq/trace" element={<DecisionTrace />} />
          <Route path="rfq/what-if" element={<WhatIfAnalysis />} />
          <Route path="rfq/recommendation" element={<Recommendation />} />
          <Route path="po" element={<PurchaseOrder />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
