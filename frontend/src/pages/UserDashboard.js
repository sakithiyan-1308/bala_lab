import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button, Card } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';
import { Eye, Download, LogOut, FileText, ClipboardList } from 'lucide-react';

export const UserDashboard = () => {
  const [reports, setReports] = useState([]);
  const { logout, user } = useAuth();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const res = await api.get('/reports');
      setReports(res.data);
    } catch (err) {
      toast.error('Failed to fetch your reports');
    }
  };

  const handleDownload = async (reportId, filename) => {
    try {
      const res = await api.get(`/reports/${reportId}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      toast.error('Download failed');
    }
  };

  const handlePreview = (reportId) => {
    const baseUrl = process.env.REACT_APP_BACKEND_URL || 'https://lab-report-hub-1.preview.emergentagent.com/api';
    const token = localStorage.getItem('token');
    window.open(`${baseUrl}/reports/${reportId}/preview?token=${token}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-primary text-white px-8 py-4 flex justify-between items-center shadow-md">
        <h1 className="text-xl font-heading font-bold">Bala Lab <span className="text-accent text-sm ml-2">Patient Portal</span></h1>
        <div className="flex items-center gap-4">
          <span className="text-sm opacity-80">{user?.email}</span>
          <Button variant="ghost" size="sm" onClick={logout} className="text-white hover:bg-white/10">
            <LogOut className="w-4 h-4 mr-2" /> Logout
          </Button>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-heading font-bold text-slate-900">Your Lab Reports</h2>
          <p className="text-slate-600">Access and download your official laboratory results securely.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reports.map(r => (
            <Card key={r.id} className="p-0 overflow-hidden group hover:shadow-md transition-shadow">
              <div className="bg-slate-100 p-8 flex justify-center items-center">
                <FileText className="w-16 h-16 text-slate-400 group-hover:text-accent transition-colors" />
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <h3 className="font-semibold text-slate-900 truncate" title={r.original_name}>
                    {r.original_name}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Uploaded on {new Date(r.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => handlePreview(r.id)}>
                    <Eye className="w-4 h-4 mr-2" /> Preview
                  </Button>
                  <Button variant="default" size="sm" className="flex-1" onClick={() => handleDownload(r.id, r.original_name)}>
                    <Download className="w-4 h-4 mr-2" /> Download
                  </Button>
                </div>
              </div>
            </Card>
          ))}
          {reports.length === 0 && (
            <Card className="col-span-full p-20 flex flex-col items-center justify-center text-slate-400 bg-white border-dashed border-2">
              <ClipboardList className="w-12 h-12 mb-4 opacity-20" />
              <p>No reports available yet. They will appear here once processed by our lab.</p>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};
