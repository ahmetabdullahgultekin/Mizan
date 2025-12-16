import { Scale } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'License',
  description: 'MIT License for the Mizan project',
};

export default function LicensePage() {
  return (
    <ComingSoon
      title="License"
      description="Mizan is open source software licensed under the MIT License. Free to use, modify, and distribute for both personal and commercial purposes."
      icon={<Scale className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
