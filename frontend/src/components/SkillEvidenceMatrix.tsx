import React, { useMemo, useState } from 'react';

export interface SkillEvidenceRow {
  skill: string;
  category: string;
  found: boolean;
  found_in_resume: string;
  occurrences: number;
  match_type: 'exact' | 'partial' | 'missing' | string;
  evidence: Array<{
    section: string;
    label?: string;
    count: number;
    snippet?: string;
  }>;
  evidence_summary: string;
}

interface SkillEvidenceMatrixProps {
  data: SkillEvidenceRow[];
}

const CATEGORY_LABELS: Record<string, string> = {
  required: 'Required',
  technical: 'Technical',
  preferred: 'Preferred',
  soft: 'Soft Skill',
};

const MATCH_BADGES: Record<string, { label: string; className: string }> = {
  exact: { label: 'Exact', className: 'bg-green-100 text-green-800' },
  partial: { label: 'Partial', className: 'bg-yellow-100 text-yellow-800' },
  missing: { label: 'Missing', className: 'bg-red-100 text-red-800' },
};

const PAGE_SIZE = 10;

export const SkillEvidenceMatrix: React.FC<SkillEvidenceMatrixProps> = ({ data }) => {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'matched' | 'partial' | 'missing'>('all');
  const [sortBy, setSortBy] = useState<'occurrences' | 'category' | 'match_type'>('category');
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    let rows = [...data];

    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (r) =>
          r.skill.toLowerCase().includes(q) ||
          r.evidence_summary.toLowerCase().includes(q) ||
          r.category.toLowerCase().includes(q)
      );
    }

    if (filter === 'matched') {
      rows = rows.filter((r) => r.match_type === 'exact');
    } else if (filter === 'partial') {
      rows = rows.filter((r) => r.match_type === 'partial');
    } else if (filter === 'missing') {
      rows = rows.filter((r) => r.match_type === 'missing');
    }

    const categoryOrder: Record<string, number> = { required: 0, technical: 1, preferred: 2, soft: 3 };
    const matchOrder: Record<string, number> = { exact: 0, partial: 1, missing: 2 };

    rows.sort((a, b) => {
      if (sortBy === 'occurrences') {
        return b.occurrences - a.occurrences || a.skill.localeCompare(b.skill);
      }
      if (sortBy === 'match_type') {
        return (
          (matchOrder[a.match_type] ?? 9) - (matchOrder[b.match_type] ?? 9) ||
          b.occurrences - a.occurrences
        );
      }
      return (
        (categoryOrder[a.category] ?? 9) - (categoryOrder[b.category] ?? 9) ||
        a.skill.localeCompare(b.skill)
      );
    });

    return rows;
  }, [data, search, filter, sortBy]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paginated = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const stats = useMemo(() => ({
    total: data.length,
    exact: data.filter((r) => r.match_type === 'exact').length,
    partial: data.filter((r) => r.match_type === 'partial').length,
    missing: data.filter((r) => r.match_type === 'missing').length,
  }), [data]);

  if (!data.length) {
    return <p className="text-gray-600">No JD skills found to compare against your resume.</p>;
  }

  return (
    <section>
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-4">
        <div>
          <h3 className="text-xl font-bold">Skill Match Evidence Matrix</h3>
          <p className="text-sm text-gray-600 mt-1">
            Every JD skill with section-level evidence from your resume
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="bg-gray-100 px-2 py-1 rounded">Total: {stats.total}</span>
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded">Exact: {stats.exact}</span>
          <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Partial: {stats.partial}</span>
          <span className="bg-red-100 text-red-800 px-2 py-1 rounded">Missing: {stats.missing}</span>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <input
          type="search"
          placeholder="Search skills or evidence..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm"
        />
        <select
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value as typeof filter);
            setPage(1);
          }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All</option>
          <option value="matched">Matched (Exact)</option>
          <option value="partial">Partial</option>
          <option value="missing">Missing</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
        >
          <option value="category">Sort by Category</option>
          <option value="occurrences">Sort by Occurrences</option>
          <option value="match_type">Sort by Match Type</option>
        </select>
      </div>

      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full text-sm min-w-[720px]">
          <thead className="bg-gray-50">
            <tr className="text-left text-gray-600 border-b">
              <th className="py-3 px-4 font-semibold">JD Skill</th>
              <th className="py-3 px-4 font-semibold">Category</th>
              <th className="py-3 px-4 font-semibold">Found in Resume</th>
              <th className="py-3 px-4 font-semibold">Occurrences</th>
              <th className="py-3 px-4 font-semibold">Match Type</th>
              <th className="py-3 px-4 font-semibold">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((row, idx) => {
              const badge = MATCH_BADGES[row.match_type] || MATCH_BADGES.missing;
              return (
                <tr key={`${row.skill}-${idx}`} className="border-b hover:bg-gray-50 align-top">
                  <td className="py-3 px-4 font-medium capitalize">{row.skill}</td>
                  <td className="py-3 px-4">
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                      {CATEGORY_LABELS[row.category] || row.category}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={row.found ? 'text-green-700 font-medium' : 'text-red-600'}>
                      {row.found_in_resume}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold">{row.occurrences}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.className}`}>
                      {badge.label}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600">
                    <p className="text-xs mb-1">{row.evidence_summary}</p>
                    {row.evidence?.length > 0 && (
                      <ul className="text-xs space-y-1">
                        {row.evidence.map((ev, i) => (
                          <li key={i} className="text-gray-500">
                            <span className="font-medium">{ev.label || ev.section}</span>
                            {' '}({ev.count}x)
                            {ev.snippet && (
                              <span className="block italic text-gray-400 truncate max-w-xs" title={ev.snippet}>
                                &ldquo;{ev.snippet}&rdquo;
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-gray-500 py-6">No skills match your search or filter.</p>
      )}

      {filtered.length > PAGE_SIZE && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <p className="text-gray-600">
            Showing {(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, filtered.length)} of {filtered.length}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="px-2 py-1">
              Page {currentPage} / {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </section>
  );
};
