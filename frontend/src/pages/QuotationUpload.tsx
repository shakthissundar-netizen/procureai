import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '../components/ui';
import { UploadCloud, File, FileText, CheckCircle2, Loader2, Play } from 'lucide-react';

export function QuotationUpload() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<{name: string, size: string, status: string}[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);

  const steps = [
    "Extracting quotation data...",
    "Validating requirements...",
    "Detecting anomalies...",
    "Calculating vendor scores...",
    "Generating recommendation..."
  ];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map(f => ({
        name: f.name,
        size: (f.size / 1024).toFixed(1) + ' KB',
        status: 'Uploaded'
      }));
      
      // Mock vendors for demo if they upload anything
      if (files.length === 0) {
         setFiles([
           { name: 'Vendor_A_ReliableTech_Quote.pdf', size: '245.1 KB', status: 'Uploaded' },
           { name: 'Vendor_B_DiscountIT_Offer.xlsx', size: '45.8 KB', status: 'Uploaded' },
           { name: 'Vendor_C_BalancedSol.pdf', size: '312.4 KB', status: 'Uploaded' }
         ]);
      } else {
         setFiles([...files, ...newFiles]);
      }
    }
  };

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isAnalyzing && analysisStep < steps.length) {
      timer = setTimeout(() => {
        setAnalysisStep(prev => prev + 1);
      }, 1200); // 1.2s per step for effect
    } else if (isAnalyzing && analysisStep === steps.length) {
      setTimeout(() => {
        navigate('/rfq/compare');
      }, 800);
    }
    return () => clearTimeout(timer);
  }, [isAnalyzing, analysisStep, navigate]);

  const startAnalysis = () => {
    setIsAnalyzing(true);
    setAnalysisStep(0);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Upload Quotations</h1>
        <p className="text-slate-500 mt-1">Upload vendor PDFs or Excel sheets for AI analysis.</p>
      </div>

      {!isAnalyzing ? (
        <>
          <Card className="border-dashed border-2 border-slate-300 bg-slate-50 hover:bg-slate-100 transition-colors">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="p-4 bg-white rounded-full shadow-sm mb-4">
                <UploadCloud className="w-8 h-8 text-primary-500" />
              </div>
              <h3 className="text-lg font-medium text-slate-900">Click to upload or drag and drop</h3>
              <p className="text-sm text-slate-500 mt-1 mb-6">PDF or Excel files up to 10MB each</p>
              
              <div className="relative">
                <input 
                  type="file" 
                  multiple 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={handleFileUpload}
                />
                <Button>Browse Files</Button>
              </div>
            </CardContent>
          </Card>

          {files.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Uploaded Vendors ({files.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {files.map((file, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg bg-white">
                      <div className="flex items-center space-x-3">
                        {file.name.endsWith('pdf') ? 
                          <FileText className="w-8 h-8 text-red-500" /> : 
                          <File className="w-8 h-8 text-green-500" />
                        }
                        <div>
                          <p className="text-sm font-medium text-slate-900">{file.name}</p>
                          <p className="text-xs text-slate-500">{file.size}</p>
                        </div>
                      </div>
                      <Badge variant="secondary">{file.status}</Badge>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 flex justify-end">
                  <Button size="lg" onClick={startAnalysis} className="w-full sm:w-auto">
                    <Play className="w-4 h-4 mr-2" />
                    Analyze Quotations
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card className="overflow-hidden border-primary-200 shadow-md">
          <div className="bg-primary-50 px-6 py-8 flex flex-col items-center text-center">
            <div className="relative mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-primary-100"></div>
              <div className="w-20 h-20 rounded-full border-4 border-primary-600 border-t-transparent animate-spin flex items-center justify-center">
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-primary-700 font-bold">{Math.round((analysisStep / steps.length) * 100)}%</span>
              </div>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">AI Analysis in Progress</h2>
            <p className="text-slate-600 max-w-md">
              ProcureAI is processing {files.length} quotations. Please wait while we extract data and calculate scores.
            </p>
          </div>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {steps.map((step, i) => {
                const isCompleted = i < analysisStep;
                const isCurrent = i === analysisStep;
                const isPending = i > analysisStep;
                
                return (
                  <div key={i} className={`flex items-center p-4 transition-colors ${isCurrent ? 'bg-blue-50/50' : ''}`}>
                    <div className="w-8 flex justify-center mr-3">
                      {isCompleted && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                      {isCurrent && <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />}
                      {isPending && <div className="w-2 h-2 rounded-full bg-slate-300"></div>}
                    </div>
                    <span className={`text-sm font-medium ${isCompleted ? 'text-slate-900' : isCurrent ? 'text-primary-700' : 'text-slate-400'}`}>
                      {step}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
