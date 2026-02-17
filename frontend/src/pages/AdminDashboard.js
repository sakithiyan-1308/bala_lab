import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button, Input, Card } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';
import { FileUp, FileText, Trash2, LogOut, User } from 'lucide-react';

export const AdminDashboard = () => {
  const [reports, setReports] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [file, setFile] = useState(null);
  const { logout, user } = useAuth();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [reportsRes, usersRes] = await Promise.all([
        api.get('/reports'),
        api.get('/users')
      ]);
      setReports(reportsRes.data);
      setUsers(usersRes.data);
    } catch (err) {
      toast.error('Failed to fetch dashboard data');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !selectedUser) {
      toast.error('Please select both a file and a user');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_email', selectedUser);

    try {
      await api.post('/reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Report uploaded successfully');
      setFile(null);
      setSelectedUser('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await api.delete(`/reports/${id}`);
      toast.success('Report deleted');
      fetchData();
    } catch (err) {
      toast.error('Delete failed');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b px-8 py-4 flex justify-between items-center shadow-sm">
        <h1 className="text-xl font-heading font-bold text-slate-900">Bala Lab <span className="text-accent text-sm ml-2 px-2 py-0.5 bg-accent/10 rounded">Admin</span></h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600">{user?.email}</span>
          <Button variant="ghost" size="sm" onClick={logout} className="text-slate-500">
            <LogOut className="w-4 h-4 mr-2" /> Logout
          </Button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-8 space-y-8">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-6 flex items-center">
            <FileUp className="w-5 h-5 mr-2 text-accent" /> Upload New Report
          </h2>
          <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Select User</label>
              <select 
                value={selectedUser} 
                onChange={(e) => setSelectedUser(e.target.value)}
                className="w-full h-10 rounded-md border border-input px-3"
              >
                <option value="">Choose a user...</option>
                {users.map(u => <option key={u.id} value={u.email}>{u.email}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Report File</label>
              <Input type="file" onChange={(e) => setFile(e.target.files[0])} />
            </div>
            <div className="flex items-end">
              <Button type="submit" className="w-full bg-accent hover:bg-accent/90">Upload Report</Button>
            </div>
          </form>
        </Card>

        <Card className="overflow-hidden">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold">Processed Reports</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b text-slate-500 text-sm font-medium">
                <tr>
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4">User Email</th>
                  <th className="px-6 py-4">Type</th>
                  <th className="px-6 py-4">Upload Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y text-sm">
                {reports.map(r => (
                  <tr key={r.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium">{r.original_name}</td>
                    <td className="px-6 py-4">{r.user_email}</td>
                    <td className="px-6 py-4 capitalize">{r.file_type}</td>
                    <td className="px-6 py-4">{new Date(r.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right">
                      <Button variant="ghost" size="icon" onClick={() => handleDelete(r.id)} className="text-error hover:text-error hover:bg-error/10">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {reports.length === 0 && (
              <div className="p-12 text-center text-slate-400">No reports found.</div>
            )}
          </div>
        </Card>
      </main>
    </div>
  );
};
