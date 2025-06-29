import React from 'react';
import '../index.css'; 
export default function ResultCard({ source, title, url }) {
  return (
    <div className="max-w-md mx-auto px-4 frosted-glass result-card-layout rounded-2xl shadow-lg text-left">
      {/* Table/Source Name - Top Left */}
      <div className="text-sm font-semibold opacity-80 mb-2">
        {source.toUpperCase()}
      </div>

      {/* Article Title */}
      <h2 className="font-heading text-base sm:text-lg font-semibold mb-4 leading-snug">
        {title}
      </h2>

      {/* View Source Link */}
      {url && ( // Only render link if URL exists
        <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="frosted-button inline-block mt-4 text-sm">
        View Source
        </a>
      )}
    </div>
  );
}
