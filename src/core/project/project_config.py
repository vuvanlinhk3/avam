"""
Project configuration manager
"""
import json
import os
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from ...models.project_config import ProjectConfig
import logging

logger = logging.getLogger(__name__)

class ProjectConfigManager:
    """Manage project configuration files"""
    
    DEFAULT_PROJECT_DIR = Path.home() / '.avam' / 'projects'
    DEFAULT_TEMPLATE_DIR = Path.home() / '.avam' / 'templates'
    
    def __init__(self, project_dir: str = None):
        """
        Initialize project config manager
        
        Args:
            project_dir: Directory to store projects (default: ~/.avam/projects)
        """
        if project_dir:
            self.project_dir = Path(project_dir)
        else:
            self.project_dir = self.DEFAULT_PROJECT_DIR
        
        # Create directories if they don't exist
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    
    def create_new_project(self, name: str = "Untitled Project") -> ProjectConfig:
        """
        Create new project configuration
        
        Args:
            name: Project name
            
        Returns:
            New ProjectConfig instance
        """
        project = ProjectConfig(name=name)
        
        # Set default output path
        output_dir = Path.cwd() / 'output'
        output_dir.mkdir(exist_ok=True)
        project.output_config.output_path = str(output_dir / f"{name}.mp4")
        
        logger.info(f"Created new project: {name}")
        return project
    
    def save_project(self, project: ProjectConfig, file_path: str = None) -> str:
        """
        Save project to file
        
        Args:
            project: ProjectConfig instance
            file_path: Path to save project (default: auto-generated)
            
        Returns:
            Path to saved project file
        """
        if not file_path:
            # Generate filename from project name
            safe_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}.avam.json"
            file_path = str(self.project_dir / filename)
        
        # Save project
        project.save(file_path)
        
        logger.info(f"Project saved: {file_path}")
        return file_path
    
    def load_project(self, file_path: str) -> ProjectConfig:
        """
        Load project from file
        
        Args:
            file_path: Path to project file
            
        Returns:
            Loaded ProjectConfig instance
        """
        project = ProjectConfig.load(file_path)
        
        logger.info(f"Project loaded: {file_path}")
        return project
    
    def list_projects(self) -> Dict[str, str]:
        """
        List all projects in project directory
        
        Returns:
            Dictionary mapping project names to file paths
        """
        projects = {}
        
        for file_path in self.project_dir.glob("*.avam.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    project_name = data.get('name', file_path.stem)
                    projects[project_name] = str(file_path)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read project file {file_path}: {e}")
        
        return projects
    
    def delete_project(self, file_path: str) -> bool:
        """
        Delete project file
        
        Args:
            file_path: Path to project file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.unlink(file_path)
            logger.info(f"Project deleted: {file_path}")
            return True
        except OSError as e:
            logger.error(f"Failed to delete project {file_path}: {e}")
            return False
    
    def create_template(self, project: ProjectConfig, template_name: str) -> str:
        """
        Create project template
        
        Args:
            project: ProjectConfig instance
            template_name: Name of template
            
        Returns:
            Path to template file
        """
        template_path = self.DEFAULT_TEMPLATE_DIR / f"{template_name}.template.json"
        
        # Save project as template
        project.save(str(template_path))
        
        logger.info(f"Template created: {template_path}")
        return str(template_path)
    
    def load_template(self, template_name: str) -> ProjectConfig:
        """
        Load project template
        
        Args:
            template_name: Name of template
            
        Returns:
            ProjectConfig from template
        """
        template_path = self.DEFAULT_TEMPLATE_DIR / f"{template_name}.template.json"
        
        if not template_path.exists():
            # Try with .json extension
            template_path = self.DEFAULT_TEMPLATE_DIR / f"{template_name}.json"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        project = ProjectConfig.load(str(template_path))
        project.name = f"New from {template_name}"
        
        logger.info(f"Template loaded: {template_path}")
        return project
    
    def list_templates(self) -> Dict[str, str]:
        """
        List all available templates
        
        Returns:
            Dictionary mapping template names to file paths
        """
        templates = {}
        
        for file_path in self.DEFAULT_TEMPLATE_DIR.glob("*.template.json"):
            template_name = file_path.stem.replace('.template', '')
            templates[template_name] = str(file_path)
        
        # Also look for regular .json files
        for file_path in self.DEFAULT_TEMPLATE_DIR.glob("*.json"):
            if '.template.' not in file_path.name:
                template_name = file_path.stem
                templates[template_name] = str(file_path)
        
        return templates
    
    def validate_project(self, project: ProjectConfig) -> Tuple[bool, List[str]]:
        """
        Validate project configuration
        
        Args:
            project: ProjectConfig to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check audio files
        if not project.audio_config.audio_files:
            errors.append("No audio files specified")
        else:
            for audio_file in project.audio_config.audio_files:
                if not os.path.exists(audio_file):
                    errors.append(f"Audio file not found: {audio_file}")
        
        # Check video segments
        if not project.video_config.video_segments:
            errors.append("No video segments specified")
        else:
            for segment in project.video_config.video_segments:
                if not os.path.exists(segment.file_path):
                    errors.append(f"Video file not found: {segment.file_path}")
        
        # Check output path
        output_dir = Path(project.output_config.output_path).parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create output directory: {output_dir}, error: {e}")
        
        # Check if output file already exists
        if os.path.exists(project.output_config.output_path):
            # This is not an error, just a warning
            logger.warning(f"Output file already exists: {project.output_config.output_path}")
        
        is_valid = len(errors) == 0
        return is_valid, errors