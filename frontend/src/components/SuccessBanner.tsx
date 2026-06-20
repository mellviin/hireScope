import React from 'react';

export const SuccessBanner: React.FC<{ message: string | null }> = ({ message }) => {
  if (!message) return null;

  return (
    <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
      {message}
    </div>
  );
};
