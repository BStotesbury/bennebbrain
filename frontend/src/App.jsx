import React, { useState} from 'react';
import MeshBackground from './components/MeshBackground';
import ResultCard from './components/ResultCard'; // Import the new ResultCard component
import './index.css'; 

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  //calling fastapi
  async function handleSearch() {
  if (!searchQuery.trim()) return;
  try {
    const response = await fetch('https://bennebbrain-production.up.railway.app/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: searchQuery }),
    });
    const data = await response.json();
    setResults(data.results || []);
  } catch (error) {
    console.error('Search failed:', error);
  }
  }
  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <MeshBackground />
      <main className="relative z-10 flex h-full w-full flex-col items-center justify-start text-center px-4 pt-16">
        <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold mt-0">
          BENNEBBRAIN
        </h1>
        <p className="mt-[48px] max-w-md font-sans text-sm sm:text-base md:text-lg">
          Enter search query below
        </p>

        {}
        <div className="mt-8 frosted-glass flex items-center rounded-full shadow-lg search-bar-layout">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
            placeholder="Search knowledgebase..."
            className="flex-grow bg-transparent outline-none border-none p-0 placeholder-gray-300 text-base text-[#f1effa]"
          />
        </div>

        {}
        <section className="result-card-layout">
          {results.map((item, index) => (
  <ResultCard
    key={index}
    source={item.source}
    title={item.text_or_title}
    url={item.source_link}
    similarity={item.similarity}
  />
))}

        </section>
      </main>
    </div>
  );
}
