import Link from "next/link";
import { AlertTriangle } from "lucide-react";

// Simple Button component matching the site theme
function SimpleButton({ children, className }: { children: React.ReactNode; className?: string }) {
    return (
        <button className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 bg-[var(--accent-primary)] text-white hover:bg-[var(--accent-hover)] ${className}`}>
            {children}
        </button>
    );
}

export default function NotFound() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-16 text-center animate-fade-in flex flex-col items-center justify-center min-h-[60vh]">
            <div className="glass rounded-xl p-8 md:p-16 border border-[var(--border-primary)] shadow-xl">
                <div className="w-24 h-24 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                    <AlertTriangle className="w-10 h-10 text-[var(--status-warning)]" />
                </div>
                <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
                    페이지를 찾을 수 없습니다
                </h1>
                <p className="text-lg text-[var(--text-secondary)] mb-8 max-w-lg mx-auto leading-relaxed">
                    요청하신 페이지가 존재하지 않거나, 주소가 변경되었을 수 있습니다.
                    <br />
                    입력하신 주소가 정확한지 다시 한 번 확인해주세요.
                </p>
                <Link href="/">
                    <SimpleButton className="shadow-lg hover:shadow-xl">
                        메인으로 돌아가기
                    </SimpleButton>
                </Link>
            </div>
        </div>
    );
}
