import React from 'react';

interface ATSScoreCardProps {
  score: number;
  title?: string;
}

export const ATSScoreCard: React.FC<ATSScoreCardProps> = ({ score, title = 'ATS Score' }) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-yellow-50';
    if (score >= 40) return 'bg-orange-50';
    return 'bg-red-50';
  };

  return (
    <div className={`${getScoreBgColor(score)} rounded-lg p-6 text-center`}>
      <h3 className="text-gray-700 font-semibold mb-2">{title}</h3>
      <div className={`text-5xl font-bold ${getScoreColor(score)}`}>
        {score.toFixed(1)}
      </div>
      <p className="text-gray-600 text-sm mt-2">out of 100</p>
      <p className="text-gray-600 text-xs mt-4">
        {score >= 80 && 'Excellent match!'}
        {score >= 60 && score < 80 && 'Good match'}
        {score >= 40 && score < 60 && 'Moderate match'}
        {score < 40 && 'Needs improvement'}
      </p>
    </div>
  );
};
