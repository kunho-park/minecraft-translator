"use client";

import { useState, useEffect, useRef } from "react";
import { Tag, X, ChevronDown, Check } from "lucide-react";

interface Category {
  id: number;
  name: string;
  slug: string;
  iconUrl: string;
}

interface TagFilterProps {
  selectedTags: string[];
  onChange: (tags: string[]) => void;
}

export default function TagFilter({ selectedTags, onChange }: TagFilterProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchCategories = async () => {
      setLoading(true);
      try {
        const response = await fetch("/api/curseforge/categories");
        if (response.ok) {
          const data = await response.json();
          setCategories(data);
        }
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && categories.length === 0) {
      fetchCategories();
    }
  }, [isOpen, categories.length]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleTag = (tagSlug: string) => {
    if (selectedTags.includes(tagSlug)) {
      onChange(selectedTags.filter((t) => t !== tagSlug));
    } else {
      onChange([...selectedTags, tagSlug]);
    }
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="relative z-50" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${isOpen
            ? "border-[var(--accent-primary)] bg-[var(--accent-primary)]/5 text-[var(--accent-primary)]"
            : "border-[var(--border-primary)] hover:border-[var(--accent-primary)]/50 hover:bg-[var(--bg-tertiary)]"
          }`}
      >
        <Tag className="w-4 h-4" />
        <span className="font-medium">태그 필터</span>
        {selectedTags.length > 0 && (
          <span className="px-2 py-0.5 bg-[var(--accent-primary)] text-white text-xs font-semibold rounded-full">
            {selectedTags.length}
          </span>
        )}
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
          <div className="sticky top-0 bg-[var(--bg-tertiary)] border-b border-[var(--border-secondary)] p-4 flex items-center justify-between">
            <h3 className="font-semibold text-[var(--text-primary)]">
              카테고리 선택
            </h3>
            {selectedTags.length > 0 && (
              <button
                type="button"
                onClick={clearAll}
                className="text-sm font-medium text-[var(--accent-primary)] hover:text-[var(--accent-hover)] transition-colors"
              >
                전체 해제
              </button>
            )}
          </div>

          <div className="max-h-72 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center">
                <div className="spinner mx-auto mb-2" />
                <span className="text-sm text-[var(--text-muted)]">로딩 중...</span>
              </div>
            ) : (
              <div className="p-2">
                {categories.map((category) => {
                  const isSelected = selectedTags.includes(category.slug);
                  return (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => toggleTag(category.slug)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${isSelected
                          ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                          : "text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                        }`}
                    >
                      {category.iconUrl && (
                        <img
                          src={category.iconUrl}
                          alt=""
                          className="w-6 h-6 rounded-lg"
                        />
                      )}
                      <span className="flex-1 text-left text-sm font-medium">
                        {category.name}
                      </span>
                      {isSelected && (
                        <Check className="w-4 h-4" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Selected tags display */}
      {selectedTags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {selectedTags.map((tagSlug) => {
            const category = categories.find((c) => c.slug === tagSlug);
            return (
              <span
                key={tagSlug}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] rounded-full text-sm font-medium border border-[var(--accent-primary)]/20"
              >
                {category?.iconUrl && (
                  <img
                    src={category.iconUrl}
                    alt=""
                    className="w-4 h-4 rounded"
                  />
                )}
                <span>{category?.name || tagSlug}</span>
                <button
                  type="button"
                  onClick={() => toggleTag(tagSlug)}
                  className="hover:bg-[var(--accent-primary)]/20 rounded-full p-0.5 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
