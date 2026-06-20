import React from 'react';

export const ErrorBanner: React.FC<{ message: string | null }> = ({ message }) => {
  if (!message) return null;

  return (
    <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
      {message}
    </div>
  );
};
