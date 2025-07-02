import React from 'react';
import '../index.css'; 

function getScoreClass(similarity) {
  if (similarity >= 0.85) return 'score-green';
  if (similarity >= 0.7) return 'score-lime';
  if (similarity >= 0.5) return 'score-amber';
  return 'score-red';
}

export default function ResultCard({ source, title, url, similarity }) {
  return (
    <div className="max-w-md mx-auto px-4 frosted-glass result-card-layout rounded-2xl shadow-lg text-left">
      
      {}
      <div className="flex items-center justify-start gap-2 mb-2">
        <div className="text-xs sm:text-sm font-semibold opacity-80">
          {source.toUpperCase()}
        </div>
        {typeof similarity === 'number' && (
          <div className={`score-pill ${getScoreClass(similarity)}`} title="Semantic similarity score">
            {(similarity * 100).toFixed(0)}%
          </div>
        )}
      </div>

      {}
      <h3 className="font-heading text-base sm:text-lg font-semibold mb-4 leading-snug">
        {title}
      </h3>

      {}
      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="frosted-button inline-block mt-4 text-sm"
        >
          View Source
        </a>
      )}
    </div>
  );
}
