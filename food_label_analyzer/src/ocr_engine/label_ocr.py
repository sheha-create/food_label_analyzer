"""
OCR Engine for extracting nutrition facts and ingredients from food labels
Supports multiple label formats including Indian packaged foods
"""
import cv2
import numpy as np
from PIL import Image
import easyocr
from typing import Dict, Tuple, Optional, List
import re
from dataclasses import dataclass
try:
    from food_label_analyzer.src.config import NutritionFacts, IngredientsList
except ImportError:
    from src.config import NutritionFacts, IngredientsList

@dataclass
class OCRResult:
    """OCR extraction result with confidence scores"""
    raw_text: str
    confidence: float
    detected_regions: Dict[str, str]  # nutrition, ingredients, etc.


class NutritionLabelOCR:
    """OCR engine for nutrition labels"""
    _shared_reader = None
    
    def __init__(self, use_easyocr: bool = True, use_tesseract: bool = False):
        """
        Initialize OCR engines
        
        Args:
            use_easyocr: Use EasyOCR (more accurate but slower)
            use_tesseract: Use Tesseract (faster)
        """
        self.use_easyocr = use_easyocr
        self.use_tesseract = use_tesseract
        
        if self.use_easyocr:
            try:
                if NutritionLabelOCR._shared_reader is None:
                    import easyocr
                    NutritionLabelOCR._shared_reader = easyocr.Reader(['en', 'hi'], gpu=False)
                self.reader = NutritionLabelOCR._shared_reader
            except Exception as e:
                print(f"EasyOCR initialization failed: {e}. Falling back to Tesseract.")
                self.use_easyocr = False
                self.use_tesseract = True
        
        if self.use_tesseract:
            import pytesseract
            # Check if tesseract is in path, or configure if needed
            # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        
        self.accuracy_metrics = {
            'ocr_attempts': 0,
            'successful_extractions': 0,
            'average_confidence': 0.0,
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image_path: Path to food label image
            
        Returns:
            Preprocessed image as numpy array
        """
        # Read image — try OpenCV first, fall back to PIL for formats like TIFF/WebP
        img = cv2.imread(image_path)
        if img is None:
            try:
                pil_img = Image.open(image_path).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception:
                raise ValueError(f"Cannot read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Adaptive thresholding works better than fixed threshold for varied lighting
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Upscale for better OCR
        scale_factor = 2
        upscaled = cv2.resize(denoised, None, fx=scale_factor, fy=scale_factor, 
                             interpolation=cv2.INTER_CUBIC)
        
        return upscaled
    
    def extract_text_easyocr(self, image_path: str) -> Tuple[str, float]:
        """Extract text using EasyOCR"""
        try:
            processed_img = self.preprocess_image(image_path)
            
            # Pass numpy array directly to EasyOCR (more compatible)
            results = self.reader.readtext(processed_img, detail=1)
            
            text_lines = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                text_lines.append(text)
                confidences.append(confidence)
            
            raw_text = "\n".join(text_lines)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return raw_text, avg_confidence
        except Exception as e:
            raise Exception(f"EasyOCR processing failed: {str(e)}")
    
    def extract_text_tesseract(self, image_path: str) -> Tuple[str, float]:
        """Extract text using Tesseract - gracefully skip if not installed"""
        try:
            import pytesseract
            processed_img = self.preprocess_image(image_path)
            
            # Convert to PIL Image
            img_pil = Image.fromarray(processed_img)
            
            # Extract text (English and Hindi)
            raw_text = pytesseract.image_to_string(img_pil, lang='eng+hin')
            
            # Get confidence scores
            data = pytesseract.image_to_data(img_pil, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
            
            return raw_text, avg_confidence
        except Exception as e:
            # Tesseract is optional - gracefully handle missing installation
            raise Exception(f"Tesseract not available: {str(e)}")
    
    def extract_from_label(self, image_path: str) -> OCRResult:
        """
        Extract text from food label image
        
        Args:
            image_path: Path to food label image
            
        Returns:
            OCRResult with extracted text and confidence
        """
        self.accuracy_metrics['ocr_attempts'] += 1
        
        raw_text = ""
        confidence = 0.0
        
        # Try EasyOCR first (more accurate)
        if self.use_easyocr:
            try:
                raw_text, confidence = self.extract_text_easyocr(image_path)
            except Exception as e:
                print(f"EasyOCR failed: {e}. Trying Tesseract...")
                self.use_easyocr = False
                self.use_tesseract = True
        
        # Try Tesseract if EasyOCR is disabled or failed
        if not raw_text and self.use_tesseract:
            try:
                raw_text, confidence = self.extract_text_tesseract(image_path)
            except Exception as e:
                print(f"Tesseract failed: {e}")
        
        if False:
            pass
        
        # Detect regions
        detected_regions = self._detect_label_regions(raw_text)
        
        if raw_text:
            self.accuracy_metrics['successful_extractions'] += 1
            self.accuracy_metrics['average_confidence'] = (
                (self.accuracy_metrics['average_confidence'] * 
                 (self.accuracy_metrics['successful_extractions'] - 1) + confidence) /
                self.accuracy_metrics['successful_extractions']
            )
        
        return OCRResult(raw_text=raw_text, confidence=confidence, detected_regions=detected_regions)
    
    def _detect_label_regions(self, text: str) -> Dict[str, str]:
        """
        Detect different regions in nutrition label
        
        Args:
            text: Raw OCR text from label
            
        Returns:
            Dictionary with identified regions
        """
        regions = {
            'nutrition_facts': '',
            'ingredients': '',
            'allergens': '',
            'serving_info': '',
        }
        
        lines = text.split('\n')
        
        # Find nutrition facts section
        nutrition_start = -1
        for i, line in enumerate(lines):
            if re.search(r'nutrition|nutritional information|पोषण|nutrition facts', 
                        line, re.IGNORECASE):
                nutrition_start = i
                break
        
        # Find ingredients section
        ingredients_start = -1
        for i, line in enumerate(lines):
            if re.search(r'ingredient|成分|सामग्री|कन्टेन्ट्स', line, re.IGNORECASE):
                ingredients_start = i
                break
        
        # Extract regions
        if nutrition_start >= 0:
            end_idx = ingredients_start if ingredients_start > nutrition_start else len(lines)
            regions['nutrition_facts'] = '\n'.join(lines[nutrition_start:end_idx])
        
        if ingredients_start >= 0:
            regions['ingredients'] = '\n'.join(lines[ingredients_start:])
        
        return regions
    
    def get_ocr_accuracy(self) -> Dict:
        """Return OCR accuracy metrics"""
        return self.accuracy_metrics.copy()


class NutritionFactsParser:
    """Parse standardized nutrition facts from OCR text"""
    
    def __init__(self):
        # Keys must match NutritionFacts dataclass field names exactly
        self.nutrition_keywords = {
            'calories': ['calorie', 'kcal', 'energy', 'cal', 'كالوري'],
            'total_fat_g': ['total fat', 'fat', 'वसा'],
            'saturated_fat_g': ['saturated fat', 'saturated', 'संतृप्त'],
            'trans_fat_g': ['trans fat', 'trans', 'ट्रांस'],
            'cholesterol_mg': ['cholesterol', 'कोलेस्ट्रॉल'],
            'sodium_mg': ['sodium', 'salt', 'na', 'सोडियम'],
            'total_carbs_g': ['total carbohydrate', 'total carb', 'carb', 'carbohydrate', 'कार्बोहाइड्रेट'],
            'dietary_fiber_g': ['dietary fiber', 'fiber', 'fibre', 'फाइबर'],
            'sugars_g': ['total sugars', 'sugar content', 'sugars', 'sugar', 'शर्करा'],
            'added_sugars_g': ['added sugars', 'added sugar', 'जोड़ा गया शर्करा'],
            'protein_g': ['protein', 'प्रोटीन'],
        }
    
    def parse_nutrition_facts(self, ocr_text: str) -> NutritionFacts:
        """
        Parse nutrition facts from OCR text - flexible parsing for various label formats
        
        Args:
            ocr_text: Raw OCR text from label
            
        Returns:
            NutritionFacts object with extracted values
        """
        nutrition = NutritionFacts(
            serving_size_grams=0,
            serving_size_unit="g",
            extraction_confidence=0.8
        )
        
        lines = ocr_text.split('\n')
        
        for line in lines:
            # Extract serving size (flexible format)
            serving_match = re.search(r'serving\s+size[:\s]+(\d+(?:\.\d+)?)\s*([a-z]*)', 
                                     line, re.IGNORECASE)
            if serving_match:
                try:
                    nutrition.serving_size_grams = float(serving_match.group(1))
                    nutrition.serving_size_unit = serving_match.group(2) or "g"
                except:
                    pass
            
            # Extract nutrients with flexible regex patterns
            for nutrient_name, keywords in self.nutrition_keywords.items():
                current_val = getattr(nutrition, nutrient_name, None)
                if current_val is not None and current_val != 0.0:
                    # Skip if already found with a real value
                    continue
                    
                for keyword in keywords:
                    # Try multiple regex patterns for flexibility
                    patterns = [
                        rf'{keyword}[:\s]+(\d+(?:\.\d+)?)\s*([a-z%]*)',  # "sugars: 7.3" or "sugars 7.3 g"
                        rf'{keyword}\s+(\d+(?:\.\d+)?)\s*([a-z%]*)',     # "sugars 7.3g"
                        rf'(\d+(?:\.\d+)?)\s*([a-z%]*)\s+{keyword}',    # "7.3 g sugars"
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            try:
                                value = float(match.group(1))
                                setattr(nutrition, nutrient_name, value)
                                break
                            except (ValueError, IndexError):
                                continue
                    
                    if getattr(nutrition, nutrient_name, None) is not None:
                        break
        
        # Calculate hidden sugars (sugars that don't have explicit "added" label)
        if nutrition.sugars_g and nutrition.sugars_g > 0:
            if nutrition.added_sugars_g is None or nutrition.added_sugars_g == 0:
                nutrition.hidden_sugars_g = nutrition.sugars_g
        elif nutrition.added_sugars_g and nutrition.added_sugars_g > 0:
            nutrition.hidden_sugars_g = nutrition.added_sugars_g
        
        nutrition.raw_extraction = ocr_text
        
        return nutrition
    
    def parse_ingredients(self, ingredients_text: str) -> IngredientsList:
        """
        Parse ingredients list from OCR text
        
        Args:
            ingredients_text: Raw ingredients section text
            
        Returns:
            IngredientsList object
        """
        ingredients_list = IngredientsList(raw_ingredients_text=ingredients_text)
        
        # Split ingredients by comma
        ingredient_items = [ing.strip() for ing in ingredients_text.split(',')]
        ingredients_list.ingredients = ingredient_items
        
        # Detect sugar indicators
        try:
            from food_label_analyzer.src.config import HIDDEN_SUGAR_KEYWORDS, HIGH_SODIUM_KEYWORDS
        except ImportError:
            from src.config import HIDDEN_SUGAR_KEYWORDS, HIGH_SODIUM_KEYWORDS
        
        for ingredient in ingredient_items:
            ingredient_lower = ingredient.lower()
            
            for sugar_keyword in HIDDEN_SUGAR_KEYWORDS:
                if sugar_keyword in ingredient_lower:
                    ingredients_list.sugar_ingredients.append(ingredient)
                    break
            
            for sodium_keyword in HIGH_SODIUM_KEYWORDS:
                if sodium_keyword in ingredient_lower:
                    ingredients_list.sodium_ingredients.append(ingredient)
                    break
            
            # Detect artificial sweeteners
            if any(x in ingredient_lower for x in ['aspartame', 'sucralose', 'saccharin', 
                                                    'stevia', 'erythritol']):
                ingredients_list.artificial_sweeteners.append(ingredient)
        
        # Extract allergens
        allergen_keywords = ['milk', 'soy', 'peanut', 'tree nut', 'wheat', 'eggs', 'fish']
        for ingredient in ingredient_items:
            ingredient_lower = ingredient.lower()
            for allergen in allergen_keywords:
                if allergen in ingredient_lower and ingredient not in ingredients_list.allergens:
                    ingredients_list.allergens.append(ingredient)
        
        ingredients_list.extraction_confidence = 0.85
        
        return ingredients_list


class LabelNormalizer:
    """Normalize nutrition facts across different label formats"""
    
    def normalize_nutrition_facts(self, nutrition: NutritionFacts, 
                                  target_serving_size_grams: float = 100) -> NutritionFacts:
        """
        Normalize nutrition facts to standard serving size
        
        Args:
            nutrition: NutritionFacts object
            target_serving_size_grams: Target serving size for normalization
            
        Returns:
            Normalized NutritionFacts
        """
        if nutrition.serving_size_grams == 0:
            return nutrition
        
        scale_factor = target_serving_size_grams / nutrition.serving_size_grams
        
        # Scale all nutrients
        nutrition.calories *= scale_factor
        nutrition.total_fat_g *= scale_factor
        nutrition.saturated_fat_g *= scale_factor
        nutrition.trans_fat_g *= scale_factor
        nutrition.cholesterol_mg *= scale_factor
        nutrition.sodium_mg *= scale_factor
        nutrition.total_carbs_g *= scale_factor
        nutrition.dietary_fiber_g *= scale_factor
        nutrition.sugars_g *= scale_factor
        nutrition.protein_g *= scale_factor
        
        if nutrition.added_sugars_g:
            nutrition.added_sugars_g *= scale_factor
        if nutrition.sugar_alcohols_g:
            nutrition.sugar_alcohols_g *= scale_factor
        
        nutrition.serving_size_grams = target_serving_size_grams
        
        return nutrition
