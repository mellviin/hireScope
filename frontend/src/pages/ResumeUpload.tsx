import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { resumeAPI } from '../services/api';
import { addResume, setError } from '../redux/slices/resumeSlice';
import { RootState } from '../redux/store';
import { ErrorBanner } from '../components/ErrorBanner';
import { SuccessBanner } from '../components/SuccessBanner';

const isValidResumeFile = (file: File) => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext === 'pdf' || ext === 'docx';
};

export const ResumeUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const dispatch = useDispatch();
  const { error } = useSelector((state: RootState) => state.resume);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!isValidResumeFile(selectedFile)) {
        dispatch(setError('Please upload a PDF or DOCX file'));
        return;
      }
      setFile(selectedFile);
      setSuccessMessage(null);
      dispatch(setError(null));
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    setSuccessMessage(null);
    try {
      const response = await resumeAPI.uploadResume(file);
      const data = response.data;

      dispatch(addResume({
        id: data.resume_id,
        filename: data.filename,
        file_type: data.file_type,
        created_at: data.created_at,
        parsed_data: data.parsed_resume,
      }));
      setFile(null);
      dispatch(setError(null));
      setSuccessMessage(`"${data.filename}" uploaded and parsed successfully.`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      dispatch(setError(typeof detail === 'string' ? detail : 'Error uploading resume'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Upload Resume</h1>

      <ErrorBanner message={error} />
      <SuccessBanner message={successMessage} />
      
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-6-12l6 6m0 0v8m0-8h-8" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          
          <p className="text-gray-600 mb-4">
            Drag and drop your resume here, or click to select
          </p>
          
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.docx"
            className="hidden"
            id="file-input"
          />
          
          <label htmlFor="file-input" className="bg-blue-600 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-700">
            Select File
          </label>
          
          {file && (
            <div className="mt-6">
              <p className="text-green-600 font-semibold">Selected: {file.name}</p>
              <button
                onClick={handleUpload}
                disabled={isLoading}
                className="mt-4 bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
              >
                {isLoading ? 'Uploading...' : 'Upload Resume'}
              </button>
            </div>
          )}
        </div>
        
        <div className="mt-6 text-sm text-gray-600">
          <p>✓ Supported formats: PDF, DOCX</p>
          <p>✓ Maximum file size: 10MB</p>
        </div>
      </div>
    </div>
  );
};
