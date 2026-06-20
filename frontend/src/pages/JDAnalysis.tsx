import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { jdAPI } from '../services/api';
import { addJobDescription, setError } from '../redux/slices/jobDescriptionSlice';
import { RootState } from '../redux/store';
import { ErrorBanner } from '../components/ErrorBanner';
import { SuccessBanner } from '../components/SuccessBanner';

export const JDAnalysis: React.FC = () => {
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [jdContent, setJdContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const dispatch = useDispatch();
  const { error } = useSelector((state: RootState) => state.jobDescription);

  const handleAnalyze = async () => {
    if (!jobTitle.trim() || !jdContent.trim()) {
      dispatch(setError('Please fill in job title and description'));
      return;
    }

    setIsLoading(true);
    setSuccessMessage(null);
    try {
      const response = await jdAPI.analyzeJD({
        job_title: jobTitle,
        company: company || undefined,
        content: jdContent,
      });
      dispatch(addJobDescription(response.data));
      dispatch(setError(null));
      setSuccessMessage(`"${response.data.job_title}" analyzed successfully. Go to Dashboard to run match analysis.`);
      setJobTitle('');
      setCompany('');
      setJdContent('');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      dispatch(setError(typeof detail === 'string' ? detail : 'Error analyzing job description'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Analyze Job Description</h1>

      <ErrorBanner message={error} />
      <SuccessBanner message={successMessage} />
      
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="mb-6">
          <label className="block text-gray-700 font-semibold mb-2">Job Title *</label>
          <input
            type="text"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g., Senior Software Engineer"
            className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-700 font-semibold mb-2">Company</label>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Company name (optional)"
            className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-700 font-semibold mb-2">Job Description *</label>
          <textarea
            value={jdContent}
            onChange={(e) => setJdContent(e.target.value)}
            placeholder="Paste the job description here..."
            rows={10}
            className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
          />
        </div>
        
        <button
          onClick={handleAnalyze}
          disabled={isLoading || !jobTitle.trim() || !jdContent.trim()}
          className="bg-blue-600 text-white px-8 py-3 rounded hover:bg-blue-700 disabled:bg-gray-400 font-semibold"
        >
          {isLoading ? 'Analyzing...' : 'Analyze Job Description'}
        </button>
      </div>
    </div>
  );
};
