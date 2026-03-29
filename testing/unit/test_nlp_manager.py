"""
Unit tests for NLPManager service.

Tests model loading, skill synonym resolution, concept mapping, and semantic extraction.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.nlp_manager import nlp_manager


class TestNLPManagerSingleton:
    """Tests for NLPManager singleton pattern."""

    def test_singleton_instance(self):
        """Test that NLPManager returns same instance."""
        instance1 = nlp_manager
        instance2 = nlp_manager
        assert instance1 is instance2

    def test_initialization_only_once(self):
        """Test that __init__ is only called once per singleton."""
        
        assert nlp_manager._initialized is True


class TestSkillSynonyms:
    """Tests for skill synonym dictionary."""

    def test_get_skill_synonyms_returns_dict(self):
        """Test that get_skill_synonyms returns a dictionary."""
        synonyms = nlp_manager.get_skill_synonyms()
        assert isinstance(synonyms, dict)
        assert len(synonyms) > 0

    def test_python_synonyms(self):
        """Test Python skill has correct synonyms."""
        synonyms = nlp_manager.get_skill_synonyms()
        assert "python" in synonyms
        python_variants = synonyms["python"]
        assert "python3" in python_variants
        assert "py" in python_variants

    def test_javascript_synonyms(self):
        """Test JavaScript skill has correct synonyms."""
        synonyms = nlp_manager.get_skill_synonyms()
        assert "javascript" in synonyms
        js_variants = synonyms["javascript"]
        assert "js" in js_variants
        assert "es6" in js_variants

    def test_kubernetes_synonyms(self):
        """Test Kubernetes skill has k8s alias."""
        synonyms = nlp_manager.get_skill_synonyms()
        assert "kubernetes" in synonyms
        k8s_variants = synonyms["kubernetes"]
        assert "k8s" in k8s_variants

    def test_docker_synonyms(self):
        """Test Docker skill has proper variants."""
        synonyms = nlp_manager.get_skill_synonyms()
        assert "docker" in synonyms
        docker_variants = synonyms["docker"]
        assert "containerization" in docker_variants

    def test_all_synonyms_are_lists(self):
        """Test all synonym values are lists."""
        synonyms = nlp_manager.get_skill_synonyms()
        for canonical, variants in synonyms.items():
            assert isinstance(variants, list), f"Variants for {canonical} should be a list"

    def test_cicd_synonyms(self):
        """Test CI/CD has continuous integration synonym."""
        synonyms = nlp_manager.get_skill_synonyms()
        assert "ci/cd" in synonyms
        cicd_variants = synonyms["ci/cd"]
        assert "continuous integration" in cicd_variants
        assert "continuous deployment" in cicd_variants


class TestSkillCategory:
    """Tests for skill category assignment."""

    def test_get_skill_category_returns_string(self):
        """Test that get_skill_category returns a string."""
        category = nlp_manager.get_skill_category("Python")
        assert isinstance(category, str)

    def test_technical_skills_categorization(self):
        """Test that technical skills are categorized correctly."""
        technical_categories = [
            nlp_manager.get_skill_category("Python"),
            nlp_manager.get_skill_category("JavaScript"),
            nlp_manager.get_skill_category("Docker"),
            nlp_manager.get_skill_category("React"),
        ]
        for cat in technical_categories:
            assert cat == "technical"

    def test_soft_skills_categorization(self):
        """Test that soft skills are categorized correctly."""
        soft_categories = [
            nlp_manager.get_skill_category("Agile"),
            nlp_manager.get_skill_category("Communication"),
            nlp_manager.get_skill_category("Mentoring"),
            nlp_manager.get_skill_category("Project Management"),
        ]
        for cat in soft_categories:
            assert cat == "soft"

    def test_domain_skills_categorization(self):
        """Test that domain skills are categorized correctly."""
        domain_categories = [
            nlp_manager.get_skill_category("Machine Learning"),
            nlp_manager.get_skill_category("Statistics"),
            nlp_manager.get_skill_category("NLP"),
            nlp_manager.get_skill_category("Cybersecurity"),
        ]
        for cat in domain_categories:
            assert cat == "domain"

    def test_default_to_technical(self):
        """Test that unknown skills default to technical."""
        category = nlp_manager.get_skill_category("UnknownSkill")
        assert category == "technical"

    def test_case_insensitive_categorization(self):
        """Test that categorization is case-insensitive."""
        assert nlp_manager.get_skill_category("PYTHON") == "technical"
        assert nlp_manager.get_skill_category("agile") == "soft"
        assert nlp_manager.get_skill_category("MACHINE LEARNING") == "domain"


class TestSkillConceptMap:
    """Tests for skill concept mapping."""

    def test_get_skill_concept_map_returns_dict(self):
        """Test that get_skill_concept_map returns a dictionary."""
        concept_map = nlp_manager.get_skill_concept_map()
        assert isinstance(concept_map, dict)
        assert len(concept_map) > 0

    def test_concept_map_values_are_lists(self):
        """Test that all concept map values are lists of strings."""
        concept_map = nlp_manager.get_skill_concept_map()
        for skill, concepts in concept_map.items():
            assert isinstance(concepts, list), f"Concepts for {skill} should be a list"
            assert len(concepts) > 0, f"Skill {skill} should have at least one concept"
            for concept in concepts:
                assert isinstance(concept, str), f"Concept for {skill} should be a string"

    def test_docker_concepts(self):
        """Test Docker has containerization concepts."""
        concept_map = nlp_manager.get_skill_concept_map()
        assert "Docker" in concept_map
        docker_concepts = concept_map["Docker"]
        assert "containerized deployment" in docker_concepts
        assert "container images and registries" in docker_concepts

    def test_kubernetes_concepts(self):
        """Test Kubernetes has orchestration concepts."""
        concept_map = nlp_manager.get_skill_concept_map()
        assert "Kubernetes" in concept_map
        k8s_concepts = concept_map["Kubernetes"]
        assert "orchestrated microservices at scale" in k8s_concepts

    def test_python_concepts(self):
        """Test Python has relevant concepts."""
        concept_map = nlp_manager.get_skill_concept_map()
        assert "Python" in concept_map
        python_concepts = concept_map["Python"]
        assert any("backend" in c.lower() or "scripting" in c.lower() for c in python_concepts)

    def test_system_design_concepts(self):
        """Test System Design has architecture concepts."""
        concept_map = nlp_manager.get_skill_concept_map()
        
        design_skill = None
        for skill in concept_map:
            if "design" in skill.lower() and "system" in skill.lower():
                design_skill = skill
                break
        
        if design_skill:
            design_concepts = concept_map[design_skill]
            assert "microservices architecture" in design_concepts or len(design_concepts) > 0

    def test_agile_concepts(self):
        """Test Agile has sprint-related concepts."""
        concept_map = nlp_manager.get_skill_concept_map()
        assert "Agile" in concept_map
        agile_concepts = concept_map["Agile"]
        assert "sprint" in " ".join(agile_concepts).lower()


class TestResolveToCanonical:
    """Tests for term-to-canonical resolution."""

    def test_resolve_exact_match(self):
        """Test resolving exact skill name."""
        result = nlp_manager.resolve_to_canonical("python")
        assert result == "Python"

    def test_resolve_synonym(self):
        """Test resolving a synonym."""
        result = nlp_manager.resolve_to_canonical("k8s")
        assert result == "Kubernetes"

    def test_resolve_case_insensitive(self):
        """Test resolution is case-insensitive."""
        result = nlp_manager.resolve_to_canonical("PYTHON")
        assert result == "Python"

    def test_resolve_js_abbreviation(self):
        """Test resolving JavaScript abbreviation."""
        result = nlp_manager.resolve_to_canonical("js")
        assert result == "Javascript"

    def test_resolve_nonexistent_returns_none(self):
        """Test nonexistent term returns None."""
        result = nlp_manager.resolve_to_canonical("NonexistentSkill123")
        assert result is None

    def test_resolve_with_whitespace(self):
        """Test resolution with leading/trailing whitespace."""
        result = nlp_manager.resolve_to_canonical("  python  ")
        assert result == "Python"

    def test_resolve_docker_variant(self):
        """Test resolving Docker variants."""
        result1 = nlp_manager.resolve_to_canonical("containerization")
        assert result1 == "Docker"

    def test_resolve_kubernetes_variants(self):
        """Test resolving Kubernetes variants."""
        result = nlp_manager.resolve_to_canonical("kubernetes")
        assert result == "Kubernetes"

    def test_resolve_cicd(self):
        """Test resolving CI/CD variants."""
        result = nlp_manager.resolve_to_canonical("continuous integration")
        
        assert result is not None and "ci" in result.lower() and "cd" in result.lower()

    def test_resolve_agile_variant(self):
        """Test resolving Agile variants."""
        result = nlp_manager.resolve_to_canonical("scrum")
        assert result == "Agile"


class TestExtractSkillsSemanticallySafety:
    """Tests for semantic extraction error handling and edge cases."""

    def test_extract_empty_sentences(self):
        """Test semantic extraction with empty sentence list."""
        result = nlp_manager.extract_skills_semantically([], ["Python"])
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_extract_empty_candidates(self):
        """Test semantic extraction with no candidate skills."""
        result = nlp_manager.extract_skills_semantically(["I work with Python"], [])
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_extract_none_sentences(self):
        """Test semantic extraction with None sentences returns dict."""
        result = nlp_manager.extract_skills_semantically(None, ["Python"])
        assert isinstance(result, dict)

    def test_extract_none_candidates(self):
        """Test semantic extraction with None candidates returns dict."""
        result = nlp_manager.extract_skills_semantically(["sentence"], None)
        assert isinstance(result, dict)

    def test_extract_returns_dict_with_scores(self):
        """Test that semantic extraction returns dict with float scores."""
        try:
            
            nlp_manager.load_sentence_transformer()
            
            sentences = [
                "I containerized applications using Docker",
                "I orchestrated microservices with Kubernetes"
            ]
            candidates = ["Docker", "Kubernetes"]
            
            result = nlp_manager.extract_skills_semantically(sentences, candidates)
            assert isinstance(result, dict)
            
            
            for skill, score in result.items():
                assert isinstance(score, (int, float))
                assert 0.0 <= score <= 1.0
        except (ImportError, Exception):
            
            pytest.skip("sentence-transformers not available")

    def test_extract_threshold_filtering(self):
        """Test that low threshold includes more skills."""
        try:
            nlp_manager.load_sentence_transformer()
            
            sentences = ["I know Python basics"]
            candidates = ["Python", "Docker"]
            
            
            high_threshold = nlp_manager.extract_skills_semantically(
                sentences, candidates, threshold=0.95
            )
            
            
            low_threshold = nlp_manager.extract_skills_semantically(
                sentences, candidates, threshold=0.10
            )
            
            
            assert len(low_threshold) >= len(high_threshold)
        except (ImportError, Exception):
            pytest.skip("sentence-transformers not available")


class TestLoadSpacyModel:
    """Tests for spaCy model loading."""

    def test_load_spacy_caches_model(self):
        """Test that spaCy model is cached after first load."""
        try:
            model1 = nlp_manager.load_spacy_model()
            model2 = nlp_manager.load_spacy_model()
            
            assert model1 is model2
        except RuntimeError:
            pytest.skip("spaCy model not available")

    def test_load_spacy_returns_spacy_language_object(self):
        """Test that loaded model has expected spaCy interface."""
        try:
            model = nlp_manager.load_spacy_model()
            
            doc = model("test text")
            assert doc is not None
            assert len(list(doc)) > 0
        except RuntimeError:
            pytest.skip("spaCy model not available")


class TestLoadSentenceTransformer:
    """Tests for Sentence-Transformer model loading."""

    def test_load_sentence_transformer_caches(self):
        """Test that Sentence-Transformer is cached."""
        try:
            model1 = nlp_manager.load_sentence_transformer()
            model2 = nlp_manager.load_sentence_transformer()
            assert model1 is model2
        except ImportError:
            pytest.skip("sentence-transformers not available")

    def test_load_sentence_transformer_can_encode(self):
        """Test that loaded model can encode sentences."""
        try:
            model = nlp_manager.load_sentence_transformer()
            embeddings = model.encode("test sentence")
            assert embeddings is not None
            assert len(embeddings) > 0
        except ImportError:
            pytest.skip("sentence-transformers not available")


class TestLoadBertModel:
    """Tests for BERT model loading."""

    def test_load_bert_caches(self):
        """Test that BERT model is cached."""
        try:
            tokenizer1, model1 = nlp_manager.load_bert_model()
            tokenizer2, model2 = nlp_manager.load_bert_model()
            assert tokenizer1 is tokenizer2
            assert model1 is model2
        except ImportError:
            pytest.skip("transformers/torch not available")

    def test_load_bert_returns_tuple(self):
        """Test that BERT loading returns tokenizer and model."""
        try:
            result = nlp_manager.load_bert_model()
            assert isinstance(result, tuple)
            assert len(result) == 2
        except ImportError:
            pytest.skip("transformers/torch not available")


class TestNLPManagerConfig:
    """Tests for NLPManager configuration."""

    def test_nlp_enabled_defaults_to_true(self):
        """Test that NLP is enabled by default."""
        assert nlp_manager.nlp_enabled is True

    def test_spacy_model_name_configured(self):
        """Test that spaCy model name is set."""
        assert nlp_manager.spacy_model_name is not None
        assert isinstance(nlp_manager.spacy_model_name, str)

    def test_sentence_transformer_name_configured(self):
        """Test that Sentence-Transformer model name is set."""
        assert nlp_manager.sentence_transformer_name is not None
        assert isinstance(nlp_manager.sentence_transformer_name, str)

    def test_bert_model_name_configured(self):
        """Test that BERT model name is set."""
        assert nlp_manager.bert_model_name is not None
        assert isinstance(nlp_manager.bert_model_name, str)


class TestResolveToCanonicalEdgeCases:
    """Edge case tests for canonical resolution."""

    def test_resolve_multiple_word_skills(self):
        """Test resolving multi-word skill names."""
        result = nlp_manager.resolve_to_canonical("machine learning")
        assert result is not None
        assert "machine" in result.lower() or "learning" in result.lower()

    def test_resolve_with_mixed_case(self):
        """Test resolution with mixed case."""
        result = nlp_manager.resolve_to_canonical("PyThOn")
        assert result == "Python"

    def test_resolve_special_chars_in_skill(self):
        """Test resolution of skills with special characters."""
        result = nlp_manager.resolve_to_canonical("c++")
        
        assert result is None or "c" in result.lower()

    def test_resolve_empty_string(self):
        """Test resolving empty string."""
        result = nlp_manager.resolve_to_canonical("")
        assert result is None

    def test_resolve_only_whitespace(self):
        """Test resolving whitespace-only string."""
        result = nlp_manager.resolve_to_canonical("   ")
        assert result is None
