import GradientBackground from "./components/GradientBackground";

export default function App() {
  return (
    
    <div className="relative h-screen w-screen overflow-hidden">
      <GradientBackground />

      <main className="z-10 flex h-full w-full 
                       flex-col items-center justify-center 
                       text-center px-4">
        <h1 className="font-heading text-4xl font-bold text-mauve">
          Welcome to BennebBrain
        </h1>
        <p className="text-mauve mt-2 max-w-md font-sans">
          Modular. Scalable. Smart.
        </p>
      </main>
    </div>
  );
}