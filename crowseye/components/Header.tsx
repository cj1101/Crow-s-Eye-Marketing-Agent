import Link from 'next/link';
import { useRouter } from 'next/router';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
}

const NavLink: React.FC<NavLinkProps> = ({ href, children }) => {
  const router = useRouter();
  const isActive = router.pathname === href;
  
  return (
    <Link 
      href={href}
      className={`px-3 py-2 rounded-md text-sm font-medium ${
        isActive 
          ? 'bg-purple-800 text-white' 
          : 'text-gray-300 hover:bg-purple-700 hover:text-white'
      }`}
    >
      {children}
    </Link>
  );
};

const Header: React.FC = () => {
  return (
    <header className="bg-purple-900 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Link href="/" className="text-white font-bold text-xl">
                Crow's Eye
              </Link>
            </div>
            <nav className="ml-10 flex items-baseline space-x-4">
              <NavLink href="/">Home</NavLink>
              <NavLink href="/media-library">Media Library</NavLink>
              <NavLink href="/gallery-generator">Gallery Generator</NavLink>
            </nav>
          </div>
          <div>
            <button className="bg-purple-700 hover:bg-purple-600 text-white px-4 py-2 rounded text-sm">
              Pro Features
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header; 