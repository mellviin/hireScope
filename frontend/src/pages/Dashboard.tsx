import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../redux/store';
import { resumeAPI, jdAPI } from '../services/api';
import { removeResume } from '../redux/slices/resumeSlice';
import { removeJobDescription } from '../redux/slices/jobDescriptionSlice';
import { ConfirmationModal } from '../components/ConfirmationModal';
import { ViewDetailModal } from '../components/ViewDetailModal';
import { ErrorBanner } from '../components/ErrorBanner';

const TrashIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

export const Dashboard: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { resumes } = useSelector((state: RootState) => state.resume);
  const { jobDescriptions } = useSelector((state: RootState) => state.jobDescription);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [selectedResumeId, setSelectedResumeId] = useState<number | ''>('');
  const [selectedJdId, setSelectedJdId] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<{ type: 'resume' | 'jd'; id: number; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewResume, setViewResume] = useState<(typeof resumes)[0] | null>(null);
  const [viewJd, setViewJd] = useState<(typeof jobDescriptions)[0] | null>(null);

  useEffect(() => {
    if (resumes.length) {
      if (!selectedResumeId || !resumes.find((r) => r.id === selectedResumeId)) {
        setSelectedResumeId(resumes[0].id);
      }
    } else {
      setSelectedResumeId('');
    }
  }, [resumes, selectedResumeId]);

  useEffect(() => {
    if (jobDescriptions.length) {
      if (!selectedJdId || !jobDescriptions.find((jd) => jd.id === selectedJdId)) {
        setSelectedJdId(jobDescriptions[0].id);
      }
    } else {
      setSelectedJdId('');
    }
  }, [jobDescriptions, selectedJdId]);

  const canAnalyze = resumes.length > 0 && jobDescriptions.length > 0;

  const handleRunAnalysis = () => {
    if (selectedResumeId && selectedJdId) {
      navigate(`/results/${selectedResumeId}/${selectedJdId}`);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    setError(null);
    try {
      if (deleteTarget.type === 'resume') {
        await resumeAPI.deleteResume(deleteTarget.id);
        dispatch(removeResume(deleteTarget.id));
      } else {
        await jdAPI.deleteJD(deleteTarget.id);
        dispatch(removeJobDescription(deleteTarget.id));
      }
      setDeleteTarget(null);
    } catch {
      setError(`Failed to delete ${deleteTarget.type === 'resume' ? 'resume' : 'job description'}.`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-4xl font-bold mb-2">Welcome, {user?.first_name || user?.username || 'there'}!</h1>
      <p className="text-gray-600 mb-8">AI-Powered Resume & Job Description Intelligence</p>

      {error && <ErrorBanner message={error} />}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-gray-600 font-semibold mb-2">Resumes Uploaded</h3>
          <div className="text-4xl font-bold text-blue-600">{resumes.length}</div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-gray-600 font-semibold mb-2">Job Descriptions Analyzed</h3>
          <div className="text-4xl font-bold text-green-600">{jobDescriptions.length}</div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-gray-600 font-semibold mb-2">Analysis Ready</h3>
          <div className="text-4xl font-bold text-purple-600">
            {canAnalyze ? '✓' : '—'}
          </div>
        </div>
      </div>

      {canAnalyze && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h3 className="text-xl font-bold mb-4">Run Match Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Select Resume</label>
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-4 py-2"
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>{r.filename}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Select Job Description</label>
              <select
                value={selectedJdId}
                onChange={(e) => setSelectedJdId(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-4 py-2"
              >
                {jobDescriptions.map((jd) => (
                  <option key={jd.id} value={jd.id}>
                    {jd.job_title}{jd.company ? ` @ ${jd.company}` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={handleRunAnalysis}
            className="bg-purple-600 text-white px-8 py-3 rounded hover:bg-purple-700 font-semibold"
          >
            Run ATS Match Analysis
          </button>
        </div>
      )}

      {/* Resume Library */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h3 className="text-xl font-bold">Resume Library</h3>
            <p className="text-sm text-gray-600">Manage your uploaded resumes</p>
          </div>
          <Link
            to="/upload"
            className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm font-semibold text-center"
          >
            Upload New
          </Link>
        </div>

        {resumes.length === 0 ? (
          <p className="text-gray-500 text-center py-6">No resumes uploaded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[500px]">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="py-2 pr-4">Resume Name</th>
                  <th className="py-2 pr-4">Upload Date</th>
                  <th className="py-2 pr-4">File Type</th>
                  <th className="py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {resumes.map((r) => (
                  <tr key={r.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 pr-4 font-medium">{r.filename}</td>
                    <td className="py-3 pr-4 text-gray-600">{formatDate(r.created_at)}</td>
                    <td className="py-3 pr-4 uppercase text-gray-600">{r.file_type}</td>
                    <td className="py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setViewResume(r)}
                          className="text-blue-600 hover:text-blue-800 font-medium px-2 py-1"
                        >
                          View
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTarget({ type: 'resume', id: r.id, name: r.filename })}
                          className="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50"
                          title="Delete resume"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* JD Library */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h3 className="text-xl font-bold">Job Description Library</h3>
            <p className="text-sm text-gray-600">Manage analyzed job descriptions</p>
          </div>
          <Link
            to="/analyze-jd"
            className="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm font-semibold text-center"
          >
            Analyze New JD
          </Link>
        </div>

        {jobDescriptions.length === 0 ? (
          <p className="text-gray-500 text-center py-6">No job descriptions analyzed yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[500px]">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="py-2 pr-4">Job Title</th>
                  <th className="py-2 pr-4">Company</th>
                  <th className="py-2 pr-4">Created Date</th>
                  <th className="py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobDescriptions.map((jd) => (
                  <tr key={jd.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 pr-4 font-medium">{jd.job_title}</td>
                    <td className="py-3 pr-4 text-gray-600">{jd.company || '—'}</td>
                    <td className="py-3 pr-4 text-gray-600">{formatDate(jd.created_at)}</td>
                    <td className="py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setViewJd(jd)}
                          className="text-blue-600 hover:text-blue-800 font-medium px-2 py-1"
                        >
                          View
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTarget({
                            type: 'jd',
                            id: jd.id,
                            name: jd.job_title,
                          })}
                          className="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50"
                          title="Delete job description"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 rounded-lg p-8 text-center">
          <h3 className="text-xl font-bold mb-4">Upload Resume</h3>
          <p className="text-gray-600 mb-4">Start by uploading your resume in PDF or DOCX format</p>
          <Link to="/upload" className="inline-block bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
            Upload Resume
          </Link>
        </div>

        <div className="bg-green-50 rounded-lg p-8 text-center">
          <h3 className="text-xl font-bold mb-4">Analyze Job Description</h3>
          <p className="text-gray-600 mb-4">Paste a job description for detailed analysis</p>
          <Link to="/analyze-jd" className="inline-block bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700">
            Analyze JD
          </Link>
        </div>
      </div>

      <ConfirmationModal
        isOpen={!!deleteTarget}
        title={deleteTarget?.type === 'resume' ? 'Delete Resume' : 'Delete Job Description'}
        message={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.name}"? This action cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />

      <ViewDetailModal
        isOpen={!!viewResume}
        title={viewResume?.filename || 'Resume Details'}
        onClose={() => setViewResume(null)}
      >
        {viewResume && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <p><span className="font-semibold">File type:</span> {viewResume.file_type.toUpperCase()}</p>
              <p><span className="font-semibold">Uploaded:</span> {formatDate(viewResume.created_at)}</p>
            </div>
            {viewResume.parsed_data?.summary && (
              <div>
                <p className="font-semibold mb-1">Summary</p>
                <p className="text-gray-600 bg-gray-50 p-3 rounded">{viewResume.parsed_data.summary}</p>
              </div>
            )}
            {viewResume.parsed_data?.skills?.length > 0 && (
              <div>
                <p className="font-semibold mb-1">Skills ({viewResume.parsed_data.skills.length})</p>
                <div className="flex flex-wrap gap-1">
                  {viewResume.parsed_data.skills.slice(0, 20).map((s: any, i: number) => (
                    <span key={i} className="bg-blue-50 text-blue-800 px-2 py-0.5 rounded text-xs">
                      {typeof s === 'string' ? s : s.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {viewResume.parsed_data?.experience?.length > 0 && (
              <div>
                <p className="font-semibold mb-1">Experience</p>
                {viewResume.parsed_data.experience.map((exp: any, i: number) => (
                  <div key={i} className="bg-gray-50 p-2 rounded mb-2">
                    <p className="font-medium">{exp.title} @ {exp.company}</p>
                    {exp.duration && <p className="text-gray-500 text-xs">{exp.duration}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </ViewDetailModal>

      <ViewDetailModal
        isOpen={!!viewJd}
        title={viewJd?.job_title || 'Job Description Details'}
        onClose={() => setViewJd(null)}
      >
        {viewJd && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <p><span className="font-semibold">Company:</span> {viewJd.company || '—'}</p>
              <p><span className="font-semibold">Created:</span> {formatDate(viewJd.created_at)}</p>
            </div>
            {viewJd.parsed_data?.required_skills?.length > 0 && (
              <div>
                <p className="font-semibold mb-1">Required Skills</p>
                <div className="flex flex-wrap gap-1">
                  {viewJd.parsed_data.required_skills.map((s: string, i: number) => (
                    <span key={i} className="bg-red-50 text-red-800 px-2 py-0.5 rounded text-xs">{s}</span>
                  ))}
                </div>
              </div>
            )}
            {viewJd.parsed_data?.preferred_skills?.length > 0 && (
              <div>
                <p className="font-semibold mb-1">Preferred Skills</p>
                <div className="flex flex-wrap gap-1">
                  {viewJd.parsed_data.preferred_skills.map((s: string, i: number) => (
                    <span key={i} className="bg-blue-50 text-blue-800 px-2 py-0.5 rounded text-xs">{s}</span>
                  ))}
                </div>
              </div>
            )}
            {viewJd.parsed_data?.responsibilities?.length > 0 && (
              <div>
                <p className="font-semibold mb-1">Responsibilities</p>
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  {viewJd.parsed_data.responsibilities.slice(0, 5).map((r: string, i: number) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </ViewDetailModal>
    </div>
  );
};
