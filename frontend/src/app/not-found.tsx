import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center p-8 text-term-text">
      <p className="text-term-orange font-mono text-lg mb-2">[404]</p>
      <h1 className="text-2xl font-mono font-semibold mb-4">
        PAGE NOT FOUND
      </h1>
      <p className="text-term-muted font-mono mb-6 text-center max-w-md">
        The requested resource could not be located. Check the URL or return to
        the terminal.
      </p>
      <Link
        href="/"
        className="font-mono px-4 py-2 bg-term-orange/20 text-term-orange border border-term-orange/50 hover:bg-term-orange/30 transition-colors"
      >
        [1] DASHBOARD
      </Link>
    </div>
  );
}
