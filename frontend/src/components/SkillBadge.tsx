import React from 'react';

interface SkillItemProps {
  skill: string;
  category?: string;
  priority?: number;
}

export const SkillBadge: React.FC<SkillItemProps> = ({ skill, category, priority = 3 }) => {
  const getPriorityColor = (p: number) => {
    if (p >= 4) return 'bg-red-100 text-red-800';
    if (p >= 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  return (
    <div className={`${getPriorityColor(priority)} px-3 py-1 rounded-full text-sm font-medium`}>
      {skill}
      {category && <span className="text-xs ml-2">({category})</span>}
    </div>
  );
};

interface SkillsListProps {
  skills: Array<{ skill: string; category?: string; priority?: number }>;
  maxDisplay?: number;
}

export const SkillsList: React.FC<SkillsListProps> = ({ skills, maxDisplay = 10 }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {skills.slice(0, maxDisplay).map((item, idx) => (
        <SkillBadge key={idx} {...item} />
      ))}
      {skills.length > maxDisplay && (
        <div className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium">
          +{skills.length - maxDisplay} more
        </div>
      )}
    </div>
  );
};
