import discord
from typing import Union
from config import BotConfig

async def is_admin(user: Union[discord.Member, discord.User]) -> bool:
    """Check if user has admin privileges"""
    if not isinstance(user, discord.Member):
        return False
    
    # Server owner is always admin
    if user.guild.owner_id == user.id:
        return True
    
    # Check if user has administrator permission
    if user.guild_permissions.administrator:
        return True
    
    # Check if user has any admin roles
    user_roles = [role.name for role in user.roles]
    return any(role in BotConfig.ADMIN_ROLES for role in user_roles)

async def has_permission(user: Union[discord.Member, discord.User], permission: str) -> bool:
    """Check if user has a specific permission"""
    if not isinstance(user, discord.Member):
        return False
    
    # Admin users have all permissions
    if await is_admin(user):
        return True
    
    # Map permission strings to Discord permissions
    permission_map = {
        'kick_members': user.guild_permissions.kick_members,
        'ban_members': user.guild_permissions.ban_members,
        'manage_messages': user.guild_permissions.manage_messages,
        'manage_channels': user.guild_permissions.manage_channels,
        'manage_guild': user.guild_permissions.manage_guild,
        'manage_roles': user.guild_permissions.manage_roles,
        'manage_nicknames': user.guild_permissions.manage_nicknames,
        'moderate_members': user.guild_permissions.moderate_members,
        'view_audit_log': user.guild_permissions.view_audit_log
    }
    
    return permission_map.get(permission, False)

def get_highest_role_position(user: discord.Member) -> int:
    """Get the position of user's highest role"""
    if not user.roles:
        return 0
    return max(role.position for role in user.roles)

def can_moderate_user(moderator: discord.Member, target: discord.Member) -> bool:
    """Check if moderator can take action against target user"""
    # Can't moderate yourself
    if moderator.id == target.id:
        return False
    
    # Server owner can moderate anyone except themselves
    if moderator.guild.owner_id == moderator.id:
        return target.id != moderator.guild.owner_id
    
    # Can't moderate server owner
    if target.guild.owner_id == target.id:
        return False
    
    # Check role hierarchy
    moderator_position = get_highest_role_position(moderator)
    target_position = get_highest_role_position(target)
    
    return moderator_position > target_position

async def check_bot_permissions(guild: discord.Guild, *permissions: str) -> dict:
    """Check if bot has required permissions in guild"""
    bot_member = guild.me
    results = {}
    
    permission_map = {
        'kick_members': bot_member.guild_permissions.kick_members,
        'ban_members': bot_member.guild_permissions.ban_members,
        'manage_messages': bot_member.guild_permissions.manage_messages,
        'manage_channels': bot_member.guild_permissions.manage_channels,
        'manage_guild': bot_member.guild_permissions.manage_guild,
        'manage_roles': bot_member.guild_permissions.manage_roles,
        'manage_nicknames': bot_member.guild_permissions.manage_nicknames,
        'moderate_members': bot_member.guild_permissions.moderate_members,
        'view_audit_log': bot_member.guild_permissions.view_audit_log,
        'send_messages': bot_member.guild_permissions.send_messages,
        'embed_links': bot_member.guild_permissions.embed_links,
        'read_message_history': bot_member.guild_permissions.read_message_history
    }
    
    for permission in permissions:
        results[permission] = permission_map.get(permission, False)
    
    return results
