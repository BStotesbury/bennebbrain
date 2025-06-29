import React from 'react';
import MeshBackground from './components/MeshBackground';

export default function App() {
  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <MeshBackground />
      <main className="relative z-10 flex h-full w-full flex-col items-center justify-start text-center px-4 pt-16">
        <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold mt-0">
          BennebBrain
        </h1>
        <p className="mt-[48px] max-w-md font-sans text-sm sm:text-base md:text-lg">
          Enter Search Query Below
        </p>

        {}
        {}
        <div className="mt-8 frosted-glass flex items-center rounded-full shadow-lg search-bar-layout">
          <input
            type="text"
            placeholder="Search knowledgebase..."
            className="flex-grow bg-transparent outline-none border-none p-0 placeholder-gray-300 text-base text-[#f1effa]"
          />
        </div>
      </main>
    </div>
  );
}
