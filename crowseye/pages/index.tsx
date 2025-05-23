import type { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';

const Home: NextPage = () => {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Crow's Eye - Marketing Automation Platform</title>
        <meta name="description" content="Smart marketing automation platform for creators and small businesses" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Crow's Eye</h1>
          <p className="text-xl text-gray-700">
            Smart marketing automation for creators and small businesses
          </p>
        </header>

        <section className="max-w-4xl mx-auto mb-16 bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-semibold mb-6">Get Started</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-purple-50 p-6 rounded-lg border border-purple-200 hover:border-purple-400 transition">
              <h3 className="text-xl font-medium text-purple-800 mb-3">Media Library</h3>
              <p className="text-gray-700 mb-4">Upload and organize your content in one place</p>
              <button 
                onClick={() => router.push('/media-library')}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition"
              >
                Open Media Library
              </button>
            </div>
            <div className="bg-indigo-50 p-6 rounded-lg border border-indigo-200 hover:border-indigo-400 transition">
              <h3 className="text-xl font-medium text-indigo-800 mb-3">Gallery Generator</h3>
              <p className="text-gray-700 mb-4">Create stunning galleries with AI assistance</p>
              <button 
                onClick={() => router.push('/gallery-generator')}
                className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition"
              >
                Create Gallery
              </button>
            </div>
          </div>
        </section>

        <section className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-semibold mb-6">Our Philosophy</h2>
          <blockquote className="italic text-xl text-gray-700 mb-6">
            "This product is the best on the market <span className="font-bold">until people wake up</span>."
          </blockquote>
          <p className="text-gray-600">
            Crow's Eye is a tool for survival in a system that rewards inauthenticity. Our goal is not to 
            entrench ourselves in that system, but to make it easier for creators to move through it — and eventually beyond it.
          </p>
        </section>
      </main>
    </div>
  );
};

export default Home; 