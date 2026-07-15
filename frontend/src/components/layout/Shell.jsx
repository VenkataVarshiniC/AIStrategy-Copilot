import Header from "./Header.jsx";

export default function Shell({ sidebar, children }) {
  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-8 px-6 py-8 lg:grid-cols-[360px_1fr]">
        <aside className="flex flex-col gap-6">{sidebar}</aside>
        <section className="flex flex-col gap-6 pb-16">{children}</section>
      </main>
    </div>
  );
}
