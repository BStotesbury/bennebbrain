import React, { useState} from 'react';
import MeshBackground from './components/MeshBackground';
import ResultCard from './components/ResultCard';
import { ToggleSwitch } from './components/ToggleSwitch';
import './index.css'; 
import ReactMarkdown from 'react-markdown';

export default function App() {
  const [isRagMode, setIsRagMode] = useState(false)
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [ragResponse, setRagResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  //calling fastapi
  async function handleSearch(e) {
  // Prevent the form from reloading the page
  e.preventDefault();
  
  if (!searchQuery.trim()) return;

  setIsLoading(true);
  setError('');
  setResults([]);
  setRagResponse(null);

  try {
    // 2. Determine the correct endpoint based on the toggle state
    const endpoint = isRagMode ? '/rag' : '/search';
    //local url 
    //const url = `http://127.0.0.1:8000${endpoint}`;
    //production url
    const url = `https://bennebbrain-production.up.railway.app${endpoint}`;
    console.log(`Sending POST request to: ${url}`);
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: searchQuery }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    if (isRagMode) {
      setRagResponse(data);
    } else {
      setResults(data.results || []);
    }

  } catch (err) {
    console.error('Search failed:', err);
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
}
  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <MeshBackground />
      <main className="relative z-10 flex h-full w-full flex-col items-center justify-start text-center px-4 pt-16">
        <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold mt-0">
          BENNEBBRAIN
        </h1>
        <div className="mt-[48px] max-w-md w-full flex justify-end">
        <ToggleSwitch isChecked={isRagMode} onToggle={setIsRagMode} />
      </div>

        {}
        <div className="mt-8 frosted-glass flex items-center rounded-full shadow-lg search-bar-layout">
          <input style={{ fontSize: '16px' }}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(e); 
              }
            }}
            placeholder="Search knowledgebase..."
            className="flex-grow bg-transparent outline-none border-none p-0 placeholder-gray-300 text-base text-[#f1effa]"
          />
        </div>

        {}
<section className="result-card-layout">
  {}
  {ragResponse && (
    <>
      <div className="frosted-glass result-card-layout p-4 mb-4 text-left text-white bg-blue-900 bg-opacity-30 rounded-lg">
        <h3 className="mb-2 font-bold text-lg">Answer</h3>
        {}
        {}
        {ragResponse.answer && (
          <div className="markdown-content">
            <ReactMarkdown>
              {ragResponse.answer}
            </ReactMarkdown>
          </div> )}
      </div>

      {}
      {ragResponse.retrieved_chunks?.map((chunk, index) => (
  <ResultCard
    key={index}
    source={`Chunk ${chunk.chunk_index}`}
    title="Retrieved Context"   
    content={chunk.chunk_text}   
    similarity={chunk.similarity}
  />
))}
    </>
  )}

  {/* Standard search results rendering */}
  {!ragResponse && results.map((item, index) => (
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
